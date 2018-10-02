# from django.contrib.auth.models import User
# from django.contrib.auth import login

# from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.staticfiles.templatetags.staticfiles import static
import requests

from .client.oauth2_client import OAuth2Client
from .client.auth_proxy import AuthClient
from .client.users_client import UsersClient
from .forms import RegistrationForm, RegistrationForm2, TextForm, ActivationForm, ActivationWithEmailForm
from .authx import *


API_KEY = settings.API_KEY
OKTA_ORG = settings.OKTA_ORG
ISSUER = settings.AUTH_SERVER_ID
CUSTOM_LOGIN_URL = settings.CUSTOM_LOGIN_URL
CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET

GOOGLE_IDP = settings.GOOGLE_IDP
FB_IDP = settings.FB_IDP
LNKD_IDP = settings.LNKD_IDP
SAML_IDP = settings.SAML_IDP

BASE_TITLE = settings.BASE_TITLE if settings.BASE_TITLE is not None else 'API Products Demo'
BASE_ICON = settings.BASE_ICON if settings.BASE_ICON is not None else '/static/img/okta-brand/logo/okta32x32.png'
DEFAULT_BACKGROUND = '/static/img/okta-brand/background/SFbayBridge.jpg'
BACKGROUND_IMAGE = settings.BACKGROUND_IMAGE_DEFAULT
BACKGROUND_IMAGE_CSS = settings.BACKGROUND_IMAGE_CSS
BACKGROUND_IMAGE_AUTHJS = settings.BACKGROUND_IMAGE_AUTHJS
BACKGROUND_IMAGE_IDP = settings.BACKGROUND_IMAGE_IDP

DEFAULT_PORT = '8000'
if settings.DEFAULT_PORT and settings.DEFAULT_PORT != 'None':
    DEFAULT_PORT = settings.DEFAULT_PORT

REDIRECT_URI = 'http://localhost:{}/oauth2/callback'.format(DEFAULT_PORT)

if settings.REDIRECT_URI and settings.REDIRECT_URI != 'None':
    REDIRECT_URI = settings.REDIRECT_URI

BASE_URL = OKTA_ORG
if CUSTOM_LOGIN_URL and CUSTOM_LOGIN_URL != 'None':
    BASE_URL = CUSTOM_LOGIN_URL

scopes = None
if settings.DEFAULT_SCOPES and settings.DEFAULT_SCOPES != 'None':
    scopes = settings.DEFAULT_SCOPES

# Option: IDP Discovery setting
IDP_DISCO_PAGE = settings.IDP_DISCO_PAGE
LOGIN_NOPROMPT_BOOKMARK = settings.LOGIN_NOPROMPT_BOOKMARK

# Option: Do Impersonation with SAML
IMPERSONATION_VERSION = settings.IMPERSONATION_VERSION if settings.IMPERSONATION_VERSION and settings.IMPERSONATION_VERSION != 'None' else 1
IMPERSONATION_ORG = settings.IMPERSONATION_ORG
IMPERSONATION_ORG_AUTH_SERVER_ID = settings.IMPERSONATION_ORG_AUTH_SERVER_ID
IMPERSONATION_ORG_OIDC_CLIENT_ID = settings.IMPERSONATION_ORG_OIDC_CLIENT_ID
IMPERSONATION_ORG_REDIRECT_IDP_ID = settings.IMPERSONATION_ORG_REDIRECT_IDP_ID
IMPERSONATION_SAML_APP_ID = settings.IMPERSONATION_SAML_APP_ID
if IMPERSONATION_ORG and IMPERSONATION_ORG != 'None' \
        and IMPERSONATION_ORG_AUTH_SERVER_ID and IMPERSONATION_ORG_AUTH_SERVER_ID != 'None' \
        and IMPERSONATION_ORG_OIDC_CLIENT_ID and IMPERSONATION_ORG_OIDC_CLIENT_ID != 'None' \
        and IMPERSONATION_ORG_REDIRECT_IDP_ID and IMPERSONATION_ORG_REDIRECT_IDP_ID != 'None' \
        and IMPERSONATION_SAML_APP_ID and IMPERSONATION_SAML_APP_ID != 'None':
    allow_impersonation = True
else:
    allow_impersonation = False
IMPERSONATION_V2_SAML_APP_ID = settings.IMPERSONATION_V2_SAML_APP_ID
IMPERSONATION_V2_ORG_API_KEY = settings.IMPERSONATION_V2_ORG_API_KEY
IMPERSONATION_V2_ORG = settings.IMPERSONATION_V2_ORG
IMPERSONATION_V2_SAML_APP_EMBED_LINK = settings.IMPERSONATION_V2_SAML_APP_EMBED_LINK
if not allow_impersonation\
    and IMPERSONATION_V2_ORG and IMPERSONATION_V2_ORG != 'None'\
    and IMPERSONATION_V2_SAML_APP_ID and IMPERSONATION_V2_SAML_APP_ID != 'None'\
    and IMPERSONATION_V2_ORG_API_KEY and IMPERSONATION_V2_ORG_API_KEY != 'None'\
    and IMPERSONATION_V2_SAML_APP_EMBED_LINK and IMPERSONATION_V2_SAML_APP_EMBED_LINK != 'None':
    allow_impersonation = True

c = {
    "org": BASE_URL,
    "iss": ISSUER,
    "aud": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "base_title": BASE_TITLE,
    "base_icon": BASE_ICON,
    "background": BACKGROUND_IMAGE if BACKGROUND_IMAGE is not None else DEFAULT_BACKGROUND,
    "background_css": BACKGROUND_IMAGE_CSS if BACKGROUND_IMAGE_CSS is not None else DEFAULT_BACKGROUND,
    "background_authjs": BACKGROUND_IMAGE_AUTHJS if BACKGROUND_IMAGE_AUTHJS is not None else DEFAULT_BACKGROUND,
    "background_idp": BACKGROUND_IMAGE_IDP if BACKGROUND_IMAGE_IDP is not None else DEFAULT_BACKGROUND,
    "idp_disco_page": IDP_DISCO_PAGE if IDP_DISCO_PAGE is not None else 'None',
    "app_permissions_claim": APP_PERMISSIONS_CLAIM,
    "api_permissions_claim": API_PERMISSIONS_CLAIM,
    "allow_impersonation": allow_impersonation
}

url_map = {}
pages_js = {}


def view_home(request):
    if is_logged_in(request):
        return HttpResponseRedirect(reverse('profile'))
    else:
        print('no profile in request')
    return view_login(request)


def not_authenticated(request):
    return render(request, 'not_authenticated.html')


def not_authorized(request):
    return render(request, 'not_authorized.html')


def view_profile(request):
    if is_logged_in(request):
        if 'entry_page' in pages_js:
            # page = 'login' if pages_js['entry_page'] == 'login_css' else pages_js['entry_page']
            page = pages_js['entry_page']
        else:
            page = 'login'

        if page in url_map:
            url_js = url_map[page]
        else:
            url_js = '/js/oidc_base.js'

        p = {'profile': json.dumps(get_profile(request)),
             "js": _do_format(request, url_js, page),
             "srv_access_token": get_access_token(request),
             "srv_id_token": get_id_token(request)
             }
        c.update(p)
    else:
        return HttpResponseRedirect(reverse('not_authenticated'))
    return render(request, 'profile.html', c)


def edit_profile(request):
    if is_logged_in(request):
        if 'entry_page' in pages_js:
            # page = 'login' if pages_js['entry_page'] == 'login_css' else pages_js['entry_page']
            page = pages_js['entry_page']
        else:
            page = 'login'

        if page in url_map:
            url_js = url_map[page]
        else:
            url_js = '/js/oidc_base.js'

        p = {'profile': get_profile(request),
             "js": _do_format(request, url_js, page)
             }
        c.update(p)
    else:
        return HttpResponseRedirect(reverse('not_authenticated'))
    return render(request, 'edit-profile.html', c)


def view_tokens(request):
    return render(request, 'tokens.html', c)


@csrf_exempt
def view_login(request, recoveryToken=None):
    unused = recoveryToken
    page = 'login'
    pages_js['entry_page'] = page
    if request.method == 'POST':
        return _do_refresh(request, page)
    else:
        c.update({"js": _do_format(request, '/js/oidc_base.js', page)})
    return render(request, 'index.html', c)


@csrf_exempt
def view_login_auto(request):
    page = 'login_noprompt'

    referrer = ''
    if 'from' in request.GET:
        referrer = request.GET['from']

    print('referrer={}'.format(referrer))
    if referrer and referrer != '':
        pages_js['entry_page'] = referrer

    if request.method == 'POST':
        return _do_refresh(request, page)
    else:
        c.update({"js": _do_format(request, '/js/get_without_prompt.js', page)})
    #Lets ensure everything is cleared out and refreshed.
    logout(request)
    return render(request, 'index_get_without_prompt.html', c)


def _do_refresh(request, key, redirect=None):
    if redirect:
        reverse_to = redirect
    else:
        reverse_to = key

    if 'Update' not in request.POST:
        if key in pages_js:
            del pages_js[key]
            print('javascript {} reset'.format(key))
        return HttpResponseRedirect(reverse(reverse_to))

    form = TextForm(request.POST)
    if form.is_valid():
        text = form.cleaned_data['myText']
        pages_js[key] = text
        print('javascript {} updated'.format(key))
        return HttpResponseRedirect(reverse(reverse_to))
    return HttpResponseRedirect('/')


def _request_url_root(request):
    scheme = request.scheme
    host = request.get_host().split(':')[0]
    meta = request.META
    port = meta['SERVER_PORT'] if 'SERVER_PORT' in meta else DEFAULT_PORT

    values = ['']*2
    values[0] = (scheme + '://' + host + ':' + port)
    values[1] = (scheme + '://' + host)
    return values


def _do_format(request, url, key, org_url=BASE_URL, issuer=ISSUER, audience=CLIENT_ID,
               idps='[]', btns='[]', embed_link=None):
    url_map.update({key: url})

    list_scopes = ['openid', 'profile', 'email']
    if scopes:
        list_scopes = scopes.split(',')
    scps = ''.join("'" + s + "', " for s in list_scopes)
    scps = '[' + scps[:-2] + ']'

    if key in pages_js:
        return pages_js[key]
    else:
        s = requests.session()
        a = requests.adapters.HTTPAdapter(max_retries=2)
        s.mount('http://', a)
        try:
            response = s.get(_request_url_root(request)[0] + static(url))
        except Exception as e:
            response = s.get(_request_url_root(request)[1] + static(url))

        text = str(response.content, 'utf-8') \
            .replace("{", "{{").replace("}", "}}") \
            .replace("[[", "{").replace("]]", "}") \
            .format(org=org_url,
                    iss=issuer,
                    aud=audience,
                    redirect=REDIRECT_URI,
                    scopes=scps,
                    idps=idps,
                    btns=btns,
                    idp_disco=embed_link,
                    impersonation_org=IMPERSONATION_ORG,
                    impersonation_org_auth_server_id=IMPERSONATION_ORG_AUTH_SERVER_ID,
                    impersonation_org_oidc_client_id=IMPERSONATION_ORG_OIDC_CLIENT_ID,
                    impersonation_org_redirect_idp_id=IMPERSONATION_ORG_REDIRECT_IDP_ID,
                    impersonation_app_embed_link=IMPERSONATION_V2_SAML_APP_EMBED_LINK)
        pages_js[key] = text
        return text


@csrf_exempt
def view_login_css(request):
    page = 'login_css'
    pages_js['entry_page'] = page
    if request.method == 'POST':
        return _do_refresh(request, page, page)
    else:
        c.update({"js": _do_format(request, '/js/oidc_css.js', page)})
    return render(request, 'index_css.html', c)


@csrf_exempt
def view_login_custom(request):
    page = 'login_custom'
    pages_js['entry_page'] = page
    if request.method == 'POST':
        return _do_refresh(request, page)
    else:
        c.update({"js": _do_format(request, '/js/custom_ui.js', page)})
    return render(request, 'index_login-form.html', c);


@csrf_exempt
def okta_hosted_login(request):
    page = 'okta_hosted_login'
    pages_js['entry_page'] = page
    c.update({"js": _do_format(request, '/js/default-okta-signin-pg.js', page)})
    return render(request, 'customized-okta-hosted.html', c)


@csrf_exempt
def view_login_idp(request):
    idps = '['
    if GOOGLE_IDP:
        if GOOGLE_IDP != 'None':
            idps += "\n      {{type: 'GOOGLE', id: '{}'}},".format(GOOGLE_IDP)
        if FB_IDP != 'None':
            idps += "\n      {{type: 'FACEBOOK', id: '{}'}},".format(FB_IDP)
        if LNKD_IDP != 'None':
            idps += "\n      {{type: 'LINKEDIN', id: '{}'}},".format(LNKD_IDP)
    idps += ']'

    btns = '['
    if SAML_IDP:
        if SAML_IDP != 'None':
            btns += "{title: 'Login SAML Idp',\n" \
                    + "        className: 'btn-customAuth',\n" \
                    + "        click: function() {\n" \
                    + "          var link =  '{issuer}/v1/authorize'\n".format(
                issuer='https://' + OKTA_ORG + '/oauth2/' + ISSUER) \
                    + "          + '?response_type=code'\n" \
                    + "          + '&client_id={client_id}'\n".format(client_id=CLIENT_ID) \
                    + "          + '&scope=openid+email+profile'\n" \
                    + "          + '&redirect_uri={redirect}'\n".format(redirect=REDIRECT_URI) \
                    + "          + '&state=foo'\n" \
                    + "          + '&nonce=foo'\n" \
                    + "          + '&idp={idp_id}'\n".format(idp_id=SAML_IDP) \
                    + "          window.location.href = link;\n" \
                    + "        }\n" \
                    + "    }"
    btns += ']'

    page = 'login_idp'
    pages_js['entry_page'] = page
    if request.method == 'POST':
        return _do_refresh(request, page)
    else:
        c.update({"js": _do_format(request, '/js/oidc_idp.js', page, idps=idps, btns=btns)})
    return render(request, 'index_idp.html', c)


# Demo: IdP discovery
@csrf_exempt
def view_login_disco(request):
    page = 'login_idp_disco'
    pages_js['entry_page'] = page
    if request.method == 'POST':
        return _do_refresh(request, page)
    else:
        c.update({"js": _do_format(request, '/js/idp_discovery.js', page, embed_link=IDP_DISCO_PAGE)})
    return render(request, 'index_idp_disco.html', c)


def view_admin(request):
    if not is_admin(request):
        return HttpResponseRedirect(reverse('not_authorized'))

    c.update({"js": _do_format(request, '/js/impersonate-delegate.js', 'admin')})
    c.update({"impersonation_version": IMPERSONATION_VERSION})
    c.update({"srv_id_token": get_id_token(request)})
    return render(request, 'admin.html', c)


def view_debug(request):
    return render(request, 'debug.html', {'meta': request.META})


def view_logout(request):
    logout(request)

    if 'entry_page' in pages_js:
        page = 'login' if pages_js['entry_page'] == 'okta_hosted_login' else pages_js['entry_page']
    else:
        page = 'login'
    print('logout back to page {}'.format(page))
    print('url = {}'.format(reverse(page)))
    c.update({"page": reverse(page)})

    # Reset the base variables in case there was impersonation event
    c.update({"org": OKTA_ORG})
    c.update({"iss": ISSUER})
    c.update({"aud": CLIENT_ID})

    return render(request, 'logged_out.html', c)


# Sample custom registration form
def registration_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            fn = form.cleaned_data['firstName']
            ln = form.cleaned_data['lastName']
            email = form.cleaned_data['email']
            pw = form.cleaned_data['password1']
            user = {
                "profile": {
                    "firstName": fn,
                    "lastName": ln,
                    "email": email,
                    "login": email
                },
                "credentials": {
                    "password": {"value": pw}
                }
            }
            client = UsersClient('https://' + OKTA_ORG, API_KEY)
            client.create_user(user=user, activate="false")

        try:
            print('create user {0} {1}'.format(fn, ln))

            return HttpResponseRedirect(reverse('registration_success'))
        except Exception as e:
            print("Error: {}".format(e))
            form.add_error(field=None, error=e)

    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})


def registration_view2(request):
    if request.method == 'POST':
        form = RegistrationForm2(request.POST)
        if form.is_valid():
            fn = form.cleaned_data['firstName']
            ln = form.cleaned_data['lastName']
            email = form.cleaned_data['email']
            user = {
                "profile": {
                    "firstName": fn,
                    "lastName": ln,
                    "email": email,
                    "login": email
                }
            }
            client = UsersClient('https://' + OKTA_ORG, API_KEY)
            client.create_user(user=user, activate="false")
        try:
            print('create user {0} {1}'.format(fn, ln))
            return HttpResponseRedirect(reverse('registration_success2'))
        except Exception as e:
            print("Error: {}".format(e))
            form.add_error(field=None, error=e)
    else:
        form = RegistrationForm2()
    return render(request, 'register2.html', {'form': form})


def activation_view(request, slug):
    name = None
    username = None
    user_id = None
    if slug:
        auth = AuthClient('https://' + OKTA_ORG)
        response = auth.recovery(slug)
        if response.status_code == 200:
            user = json.loads(response.content)['_embedded']['user']
            name = user['profile']['firstName']
            username = user['profile']['login']
            user_id = user['id']
        else:
            return HttpResponseRedirect(reverse('not_authenticated'))

    if request.method == 'POST':
        if user_id is None:
            return HttpResponseRedirect(reverse('not_authenticated'))

        try:
            form = ActivationForm(request.POST)
            if form.is_valid():
                pw = form.cleaned_data['password1']
                user = {
                    "credentials": {
                        "password": {"value": pw}
                    }
                }
                client = UsersClient('https://' + OKTA_ORG, API_KEY)
                client.set_password(user_id=user_id, user=user)
                res = auth.authn(username, pw)
                if res.status_code == 200:
                    session_token = json.loads(res.content)['sessionToken']
                    return redirect('https://' + OKTA_ORG + LOGIN_NOPROMPT_BOOKMARK + '?sessionToken={}'.format(session_token))

            return HttpResponseRedirect(reverse('registration_success'))
        except Exception as e:
            print("Error: {}".format(e))
            form.add_error(field=None, error=e)
    else:
        form = ActivationForm()
    return render(request, 'activate.html', {'form': form, 'slug': slug, 'firstName': name})


# A custom registration flow where user is created STAGED. Then an OTP is sent via Email to activate the account
def activation_wo_token_view(request):
    state = None
    if request.method == 'POST':
        form = ActivationWithEmailForm(request.POST)
        if form.is_valid():
            state = request.session['activation_state']
            print('state={}'.format(state))

            email = form.cleaned_data['email']
            print('email={}'.format(email))
            otp = form.cleaned_data['verificationCode']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

            client = UsersClient('https://' + OKTA_ORG, API_KEY)
            user = json.loads(client.get_user(email))

            if state == 'verify-email':
                for key in list(request.session.keys()):
                    if key in ['activation_state', 'email_factor_id', 'verification_username', 'verification_user_id']:
                        del request.session[key]

                request.session['activation_state'] = 'verify-token'
                if user['status'] == 'STAGED':
                    enroll_status = client.enroll_email_factor(user['id'], email)
                    #if enroll_status.status_code == 200:
                    response = client.list_factors(user['id'])
                    factors = json.loads(response)
                    for factor in factors:
                        if factor['factorType'] == 'email':
                            request.session['email_factor_id'] = factor['id']
                            request.session['verification_username'] = email
                            request.session['verification_user_id'] = user['id']
                            client.verify_email_factor(user['id'], factor['id'])
                            break

            elif state == 'verify-token':
                request.session['activation_state'] = 'set-password'
                response = client.verify_email_factor(user_id=request.session['verification_user_id'],
                                                      factor_id=request.session['email_factor_id'],
                                                      pass_code=otp)
            elif state == 'set-password':
                payload = {
                    "credentials": {
                        "password": {"value": password1}
                    }
                }
                setpassword = client.set_password(user_id=request.session['verification_user_id'], user=payload)
                activate = client.activate(user_id=request.session['verification_user_id'])
                auth = AuthClient('https://' + OKTA_ORG)
                res = auth.authn(request.session['verification_username'], password1)
                if res.status_code == 200:
                    session_token = json.loads(res.content)['sessionToken']
                    return redirect('https://' + OKTA_ORG + IDP_DISCO_PAGE + '?sessionToken={}'.format(session_token))
        else:
            print('invalid form')
    else:
        state = 'verify-email'
        request.session['activation_state'] = state
        form = ActivationWithEmailForm()

    return render(request, 'activate_w_email.html', {'form': form, 'state': state})


def registration_success(request):
    return render(request, 'success.html')


def registration_success2(request):
    return render(request, 'success2.html')


def oauth2_callback(request):
    return render(request, 'oauth2_callback.html')


@csrf_exempt
def oauth2_post(request):
    access_token = None
    id_token = None
    code = None
    if request.method == 'POST':
        print('POST request: {}'.format(request.POST))
        if 'code' in request.POST:
            code = request.POST['code']
        if 'access_token' in request.POST:
            access_token = request.POST['access_token']
        if 'id_token' in request.POST:
            id_token = request.POST['id_token']

        # special impersonation logic overrides the org variables
        if 'org' in request.POST:
            if request.POST['org'] == IMPERSONATION_ORG:
                c.update({'org': request.POST['org']})
                c.update({'aud': IMPERSONATION_ORG_OIDC_CLIENT_ID})
                c.update({'iss': IMPERSONATION_ORG_AUTH_SERVER_ID})

    elif request.method == 'GET':
        print('GET request: {}'.format(request.GET))
        # print('state={}'.format(request.COOKIES["okta-oauth-state"]))
        # print('nonce={}'.format(request.COOKIES["okta-oauth-nonce"]))

        if 'code' in request.GET:
            code = request.GET['code']
        if 'state' in request.GET:
            state = request.GET['state']

    if code:
        client = OAuth2Client('https://' + OKTA_ORG, CLIENT_ID, CLIENT_SECRET)
        tokens = client.token(code, REDIRECT_URI, ISSUER)
        print(print('Tokens from the code retrieval {}'.format(tokens)))
        if tokens['access_token']:
            access_token = tokens['access_token']

        if tokens['id_token']:
            id_token = tokens['id_token']

    if access_token:
        # In the real world, you should validate the access_token. But this demo app is going to skip that part.
        print('access_token = {}'.format(access_token))

        client = OAuth2Client('https://' + OKTA_ORG)
        profile = client.profile(access_token)
        set_profile(request, profile)
        set_access_token(request, access_token)

    if id_token:
        # In the real world, you should validate the id_token. But this demo app is going to skip that part.
        print('id_token = {}'.format(id_token))
        set_id_token(request, id_token)

    return HttpResponseRedirect(reverse('home'))


# IMPERSONATION Demo
def login_delegate(request):
    if 'profile' in request.session:
        del request.session['profile']
    for key in list(request.session.keys()):
        del request.session[key]

    c.update({"js": _do_format(request, '/js/login-delegate.js', 'login_delegate')})
    return render(request, 'login_delegate.html', c)


@csrf_exempt
def process_creds(request):
    print('#####################################PROCESS CREDS#####################################')
    print(request.POST)
    print('#####################################PROCESS CREDS#####################################')

    response = HttpResponse()
    response.content = 'OK!'
    response.status_code = 200
    return response


# def view_login_baybridge(request):
#     return render(request, 'z-login-baybridge.html');

# def view_login_brooklynbridge(request):
#     return render(request, 'z-login-brooklynbridge.html');

# def hellovue(request):
#     return render(request, 'z-hellovue.html');


# def proxy_callback(request):
#     if 'profile' in request.session:
#         del request.session['profile']
#     for key in list(request.session.keys()):
#         del request.session[key]
#     return render(request, 'z-proxy-callback.html')


# @csrf_exempt
# def auth_broker(request):
#     print(request)
#     cookies = request.COOKIES
#     print('cookie: {}'.format(cookies))
#
#     response = HttpResponse()
#     response.status_code = 200
#
#     if request.method == 'POST':
#         body = json.loads(request.body)
#         username = body['username']
#         password = body['password']
#         auth = AuthClient('https://' + OKTA_ORG)
#         res = auth.authn(username, password)
#         print('status={}'.format(res.status_code))
#         response.status_code = res.status_code
#
#         content = json.dumps(res.json())
#         print('response={}'.format(content))
#         response.content = content
#
#         return response
#
#     return response
#
#
# def sessions_broker(request):
#     print(request)
#     response = HttpResponse()
#     response.status_code = 200
#
#     cookies = request.COOKIES
#     print('cookie: {}'.format(cookies))
#
#     auth = SessionsClient('https://' + OKTA_ORG)
#     res = auth.me()
#     response.status_code = res.status_code
#     content = json.dumps(res.json())
#     print('response={}'.format(content))
#     response.content = content
#
#     return response
