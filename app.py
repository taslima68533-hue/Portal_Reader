"""Portal UI mirror. Upstream API credentials stay on this server."""
import hashlib,hmac,json,os,re,secrets,ssl,time,threading
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,urlopen,HTTPRedirectHandler,build_opener,HTTPSHandler
from urllib.error import HTTPError,URLError
from flask import Flask,request,session,redirect,Response,render_template,abort
from dotenv import load_dotenv
load_dotenv(Path(__file__).with_name('.env'))
API_BASE=os.environ.get('PORTAL_API_BASE','https://hridoybothub.online/api/v1').rstrip('/')
API_KEY=os.environ.get('PORTAL_API_KEY','')
SECRET=os.environ.get('READER_SESSION_SECRET','')
parsed=urlsplit(API_BASE)
if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
    raise RuntimeError('PORTAL_API_BASE must be a fixed HTTPS API URL')
if not API_KEY or API_KEY.startswith('REPLACE_') or len(SECRET)<32 or SECRET.startswith('REPLACE_'):
    raise RuntimeError('Set PORTAL_API_KEY and a random READER_SESSION_SECRET (environment variables or .env)')
app=Flask(__name__)
app.config.update(SECRET_KEY=SECRET,MAX_CONTENT_LENGTH=65536,SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=os.environ.get('READER_COOKIE_SECURE','true').lower()=='true')
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
opener=build_opener(NoRedirect(),HTTPSHandler(context=ssl.create_default_context()))

def upstream(endpoint,params=None,method='GET',body=None,form=None):
    # The client never accepts a user-supplied host, path or proxy URL.
    if endpoint not in ('portal/page','portal/status','portal/message','portal/reactivate','portal/start','portal/logo'):
        raise ValueError('Unsupported API endpoint')
    url=API_BASE+'/'+endpoint+('?' + urlencode(params) if params else '')
    headers={'X-API-Key':API_KEY,'Accept':'application/json' if endpoint!='portal/page' else 'text/html','User-Agent':'PortalInboxReader/1.0'}
    data=None
    if body is not None:data=json.dumps(body).encode();headers['Content-Type']='application/json'
    elif form is not None:data=urlencode(form).encode();headers['Content-Type']='application/x-www-form-urlencoded'
    try:
        response=opener.open(Request(url,data=data,headers=headers,method=method),timeout=15)
    except HTTPError as exc:response=exc
    except (URLError,TimeoutError,OSError):return b'{"ok":false,"error":"portal_temporarily_unavailable"}',503,{'Content-Type':'application/json','Retry-After':'5'}
    with response:
        content=response.read(2*1024*1024+1)
        if len(content)>2*1024*1024:return b'{"ok":false,"error":"response_too_large"}',502,{'Content-Type':'application/json'}
        return content,response.status,dict(response.headers.items())

def code_value(value):
    code=str(value or '').strip().upper()
    if not re.fullmatch(r'[A-Z0-9]{6,32}',code):abort(404)
    return code

def remember(code):
    allowed=list(session.get('codes') or [])
    if code not in allowed:allowed.append(code)
    session['codes']=allowed[-50:]

def authorize(code):
    code=code_value(code)
    if code not in (session.get('codes') or []):abort(403)
    return code

def csrf():
    if 'csrf' not in session:session['csrf']=secrets.token_urlsafe(32)
    return session['csrf']

@app.before_request
def check_csrf():
    if request.method=='POST':
        expected=session.get('csrf') or ''
        supplied=request.headers.get('X-CSRF-Token') or request.form.get('csrf') or ''
        if not expected or not hmac.compare_digest(expected,supplied):abort(403)

@app.after_request
def private_response(response):
    response.headers['Cache-Control']='private, no-store, max-age=0'
    response.headers['Pragma']='no-cache';response.headers['Referrer-Policy']='no-referrer';response.headers['X-Content-Type-Options']='nosniff'
    return response

def decorate_page(content):
    # Only the public display HTML is copied. No upstream API key is emitted.
    text=content.decode('utf-8','replace');token=csrf()
    hidden='<input type="hidden" name="csrf" value="'+token+'">'
    text=re.sub(r'(<form\b[^>]*>)',lambda m:m[0]+hidden,text,flags=re.I)
    script='<script>(function(){const token='+json.dumps(token)+';const original=window.fetch;window.fetch=function(input,options){options=options||{};const u=new URL(typeof input==="string"?input:input.url,location.href);if(u.origin===location.origin&&String(options.method||"GET").toUpperCase()==="POST"){const headers=new Headers(options.headers||{});headers.set("X-CSRF-Token",token);options={...options,headers};}return original.call(this,input,options);};})();</script>'
    text=text.replace('</head>',script+'</head>',1)
    # Keep the original UI on temporary errors, and honor rate-limit backoff.
    text=text.replace('let _pollBusy=false;','let _pollBusy=false; let _readerRetryAfter=0;')
    text=text.replace("    updateTimerState(j);","    if(!j.ok){_readerRetryAfter=Number(r.headers.get('Retry-After')||5);return;} _readerRetryAfter=0;\n    updateTimerState(j);")
    text=text.replace('if(_endPolls<2){setTimeout(pollLoop,2000);}','if(_endPolls<2){setTimeout(pollLoop,Math.max(2000,_readerRetryAfter*1000));}')
    return text

@app.route('/',methods=['GET','POST'])
@app.route('/OTP',methods=['GET','POST'])
@app.route('/OTP/',methods=['GET','POST'])
def enter():
    if request.method=='POST':
        code=code_value(request.form.get('code'));remember(code);return redirect('/OTP/'+code)
    content,status,headers=upstream('portal/page',{'page':'enter'})
    if status==200 and 'text/html' in headers.get('Content-Type',''):
        return Response(decorate_page(content),mimetype='text/html')
    body="<div class='card form-card'><div class='status-icon'>🔐</div><h1>Open your OTP session</h1><p>Enter your redeem code to open the temporary inbox.</p><form method='post'><div class='form-row'><input name='code' placeholder='ENTER REDEEM CODE' maxlength='32' required autocomplete='off'></div><button class='btn btn-primary full'>Continue to Inbox →</button></form></div>"
    page=render_template('page.html',body=body,code='',poll=False,left='',expired=False,can_reactivate=False,reactivate_lease=[],reactivate_time_up=False,countdown_initial_sec=0)
    return Response(decorate_page(page.encode()),mimetype='text/html')

def proxy_page(code,mode):
    code=code_value(code)
    # Direct code links are bearer credentials, just like the original Portal.
    if request.method=='GET':remember(code)
    else:authorize(code)
    form=None
    if request.method=='POST':
        form={k:request.form[k] for k in ('action','new_code','redeem_code') if k in request.form}
    content,status,headers=upstream('portal/page',{'code':code,'page':mode},request.method,form=form)
    if headers.get('Content-Type','').startswith('application/json'):
        try:result=json.loads(content)
        except ValueError:result={}
        target=result.get('redirect') or ''
        if re.fullmatch(r'/OTP/[A-Za-z0-9]{6,32}(?:/(?:new-mail|buy-again|how-to-use))?',target):
            destination=target.split('/')[2];remember(destination)
            return redirect(target,code=307 if result.get('redirect_status')==307 else 303)
        message='This code is unavailable.' if status in (404,410) else 'The inbox is temporarily unavailable. Please try again shortly.'
        page=render_template('page.html',body="<div class='card status-card'><h1>Inbox unavailable</h1><p>"+message+"</p></div>",code='',poll=False,left='',expired=False,can_reactivate=False,reactivate_lease=[],reactivate_time_up=False,countdown_initial_sec=0)
        return Response(decorate_page(page.encode()),status=status,mimetype='text/html')
    return Response(decorate_page(content),status=status,mimetype='text/html')

@app.route('/OTP/<code>',methods=['GET','POST'])
def inbox(code):return proxy_page(code,'session')
@app.route('/OTP/<code>/new-mail',methods=['GET','POST'])
def new_mail(code):return proxy_page(code,'new-mail')
@app.route('/OTP/<code>/buy-again',methods=['GET','POST'])
def buy_again(code):return proxy_page(code,'buy-again')
@app.route('/OTP/<code>/how-to-use')
def how_to_use(code):return proxy_page(code,'how-to-use')

@app.route('/OTP/<code>/status')
def status(code):
    code=authorize(code);raw,status,headers=upstream('portal/status',{'code':code})
    try:
        result=json.loads(raw)
        for field in ('mails','history_mails'):
            for mail in result.get(field) or []:
                if mail.get('body_endpoint') and re.fullmatch(r'[0-9a-f]{64}',str(mail.get('id') or '')):
                    mail['body_url']='/OTP/'+code+'/message/'+mail['id']
        raw=json.dumps(result).encode()
    except (ValueError,TypeError):raw=b'{"ok":false,"error":"portal_temporarily_unavailable"}';status=502
    response=Response(raw,status=status,mimetype='application/json')
    if headers.get('Retry-After'):response.headers['Retry-After']=headers['Retry-After']
    return response

@app.route('/OTP/<code>/reactivate',methods=['POST'])
def reactivate(code):
    code=authorize(code);body=request.get_json(silent=True) or {}
    if not isinstance(body,dict):abort(400)
    data={k:body[k] for k in ('lease','session_token','reason') if k in body};data['code']=code
    raw,status,headers=upstream('portal/reactivate',method='POST',body=data)
    response=Response(raw,status=status,mimetype='application/json')
    if headers.get('Retry-After'):response.headers['Retry-After']=headers['Retry-After']
    return response

@app.route('/OTP/<code>/message/<message_id>')
def message(code,message_id):
    code=authorize(code)
    if not re.fullmatch(r'[0-9a-f]{64}',message_id):abort(404)
    raw,status,headers=upstream('portal/message',{'code':code,'message_id':message_id})
    response=Response(raw,status=status,mimetype='text/html' if status==200 else 'text/plain')
    response.headers['Content-Security-Policy']="default-src 'none'; sandbox allow-popups allow-popups-to-escape-sandbox; base-uri 'none'; form-action 'none'"
    return response

_logo_cache={}
_logo_lock=threading.Lock()
@app.route('/OTP/logo/<name>')
def logo(name):
    if len(name)>100 or any(ord(c)<32 or c in '/\\' for c in name):abort(404)
    with _logo_lock:cached=_logo_cache.get(name)
    if cached and time.time()-cached[0]<3600:
        raw,status,headers=cached[1]
    else:
        raw,status,headers=upstream('portal/logo',{'name':name})
        ctype=headers.get('Content-Type','').split(';')[0]
        if status!=200 or not ctype.startswith('image/') or len(raw)>512000:abort(404)
        with _logo_lock:
            if len(_logo_cache)>=128:_logo_cache.pop(next(iter(_logo_cache)))
            _logo_cache[name]=(time.time(),(raw,status,headers))
    response=Response(raw,status=status,mimetype=headers.get('Content-Type','image/png'))
    # Uploaded SVG is used as an image, not an active HTML document.
    response.headers['Content-Security-Policy']="default-src 'none'; sandbox"
    return response

if __name__=='__main__':app.run(host='127.0.0.1',port=int(os.environ.get('PORT','5000')),debug=False)
