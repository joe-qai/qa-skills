#!/usr/bin/env python3
"""
禅道 (ZenTao) 客户端 —— 提交 Bug / 上传附件

基于 zentao-cli 的设计思路，支持：
- API v1 REST（标准流程，适用于 ZenTao 20+）
- Session Cookie 认证（适用于旧版本实例，如 ZenTao 18.x）
- 多行步骤内容（自动转 HTML 换行）
- 附件上传（REST /files + Web 表单双通道）

环境变量（可替代命令行参数）：
  ZENTAO_URL, ZENTAO_ACCOUNT, ZENTAO_PASSWORD, ZENTAO_VERIFY_SSL (0/1)
"""

import os
import sys
import json
import uuid
import re
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("错误：缺少 requests 库，请运行 pip install requests", file=sys.stderr)
    sys.exit(1)


# ──────────────────────────── 客户端类 ────────────────────────────

class ZentaoClient:
    """禅道客户端，支持 REST API v1 和 Session Cookie 两种方式。"""

    def __init__(self, base_url, account, password, verify_ssl=True, debug=False):
        self.base_url = base_url.rstrip('/')
        self.api_v1 = self.base_url + '/api.php/v1'
        self.account = account
        self.password = password
        self.verify_ssl = verify_ssl
        self.debug = debug
        self.timeout = 30
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    # ── 底层请求 ──

    def _request(self, method, path, *, params=None, json_data=None,
                 data=None, files=None, headers=None):
        url = self.api_v1 + path
        req_headers = {}
        if headers:
            req_headers.update(headers)
        if self.token:
            req_headers['Token'] = self.token
        if files:
            req_headers.pop('Content-Type', None)

        if self.debug:
            print(f"[DEBUG] {method} {url}", file=sys.stderr)
            if json_data:
                print(f"[DEBUG] body: {json.dumps(json_data, ensure_ascii=False)[:500]}", file=sys.stderr)
            print(f"[DEBUG] headers: {req_headers}", file=sys.stderr)

        resp = self.session.request(
            method, url, params=params, json=json_data,
            data=data, files=files, headers=req_headers or None,
            verify=self.verify_ssl, timeout=self.timeout,
        )

        if self.debug:
            print(f"[DEBUG] response: {resp.status_code} {resp.text[:500]}", file=sys.stderr)

        return self._parse_response(resp)

    @staticmethod
    def _parse_response(resp):
        try:
            body = resp.json()
        except ValueError:
            body = resp.text

        if resp.status_code >= 400:
            raise RuntimeError(
                f"HTTP {resp.status_code} {resp.reason} | URL: {resp.url} | "
                f"Response: {json.dumps(body, ensure_ascii=False)[:500]}"
            )
        if isinstance(body, dict) and body.get('error'):
            raise RuntimeError(f"禅道接口错误: {json.dumps(body, ensure_ascii=False)[:500]}")
        return body

    def _request_raw(self, method, url, **kwargs):
        """发送原始请求（不拼接 api_v1 前缀），用于 Session Cookie 认证。"""
        headers = kwargs.pop('headers', {}) or {}
        if self.token:
            headers['Token'] = self.token
        if self.debug:
            print(f"[DEBUG] RAW {method} {url}", file=sys.stderr)
            print(f"[DEBUG] RAW headers: {headers}", file=sys.stderr)
        # 提取 timeout，避免重复传入
        timeout = kwargs.pop('timeout', self.timeout)
        resp = self.session.request(method, url, headers=headers or None,
                                    verify=self.verify_ssl, timeout=timeout, **kwargs)
        if self.debug:
            print(f"[DEBUG] RAW response: {resp.status_code} {resp.text[:300]}", file=sys.stderr)
        return resp

    # ── 认证 ──

    def login(self):
        """POST /tokens 用账号密码换取 token。"""
        resp = self.session.post(
            self.api_v1 + '/tokens',
            json={'account': self.account, 'password': self.password},
            verify=self.verify_ssl, timeout=30,
        )
        body = self._parse_response(resp)
        self.token = body.get('token')
        if not self.token:
            raise RuntimeError(f"登录失败，未返回 token: {json.dumps(body, ensure_ascii=False)[:500]}")
        return self.token

    def ensure_login(self):
        if not self.token:
            self.login()
        return self.token

    def login_via_cookie(self):
        """通过 Session Cookie 登录（兼容旧版实例）。"""
        resp = self.session.post(
            self.base_url + '/api.php?m=user&f=login',
            data={'account': self.account, 'password': self.password},
            verify=self.verify_ssl, timeout=30,
        )
        body = self._parse_response(resp)
        if body.get('status') != 'success':
            raise RuntimeError(f"Cookie 登录失败: {body}")
        return True

    # ── 产品 / 模块 / 版本 / 用户 ──

    def get_products(self, limit=100):
        self.ensure_login()
        return self._request('GET', '/products', params={'limit': limit})

    def get_modules(self, product_id, module_type='bug'):
        self.ensure_login()
        return self._request('GET', f'/modules?type={module_type}&id={product_id}')

    def get_builds(self, product_id=None, project_id=None, limit=100):
        self.ensure_login()
        params = {'limit': limit}
        if product_id:
            params['type'] = 'product'
            params['param'] = product_id
        elif project_id:
            params['project'] = project_id
        return self._request('GET', '/builds', params=params)

    def get_execution(self, product_id, limit=20):
        self.ensure_login()
        r = self._request('GET', '/executions', params={'product': product_id, 'limit': limit})
        executions = r.get('executions', [])
        return executions[0]['id'] if executions else None

    def fuzzy_match_build(self, product_id, build_name, limit=100):
        self.ensure_login()
        try:
            r = self._request('GET', '/bugs', params={'product': product_id, 'limit': limit})
        except Exception:
            return build_name
        builds = set()
        for b in r.get('bugs', []):
            ob = b.get('openedBuild')
            if ob:
                if isinstance(ob, list):
                    for x in ob:
                        if isinstance(x, dict):
                            bid = x.get('id', '')
                            if bid:
                                builds.add(str(bid))
                        else:
                            s = str(x)
                            if s:
                                builds.add(s)
                else:
                    s = str(ob)
                    if s:
                        builds.add(s)
        if not builds:
            return build_name
        if build_name in builds:
            return build_name
        candidates = [b for b in builds if build_name in b or b in build_name]
        return candidates[0] if candidates else build_name

    def get_users(self, limit=200):
        self.ensure_login()
        return self._request('GET', '/users', params={'limit': limit})

    # ── 步骤内容处理（多行换行） ──

    @staticmethod
    def steps_to_html(steps_text):
        """
        将步骤文本传递给 API。
        
        部分禅道实例会在服务端对 steps 做 HTML 转义（存储为 &lt; 而非 <），
        因此客户端直接发送纯文本即可，由服务端处理换行显示。
        若实例已支持 HTML steps 字段，用户可手动传入带 <p> 标签的内容。
        """
        return steps_text

    # ── Bug 创建 ──

    def create_bug(self, product_id, title, severity, pri, opened_build,
                   steps, module=None, assigned_to=None, bug_type='codeerror',
                   project=None, execution=None, os_name=None, browser=None,
                   keywords=None, mailto=None, deadline=None, uid=None,
                   story=None, task=None, **extra):
        """
        POST /products/<product_id>/bugs 创建 Bug。
        兼容 zentao-cli 风格：同时传 productID 到 query string（部分实例需要）。
        """
        self.ensure_login()
        # opened_build 规范化
        if isinstance(opened_build, (int, str)):
            opened_build = [opened_build]
        resolved = []
        for b in opened_build:
            s = str(b)
            matched = self.fuzzy_match_build(product_id, s)
            try:
                resolved.append(int(matched))
            except ValueError:
                resolved.append(matched)
        opened_build = resolved

        # 自动注入 execution
        if execution is None:
            try:
                exec_id = self.get_execution(product_id)
                if exec_id is not None:
                    execution = exec_id
            except Exception:
                pass

        payload = {
            'title': title,
            'severity': int(severity),
            'pri': int(pri),
            'type': bug_type,
            'openedBuild': opened_build,
            'steps': steps,
        }
        if module is not None:
            payload['module'] = int(module)
        if assigned_to:
            payload['assignedTo'] = assigned_to
        if project is not None:
            payload['project'] = int(project)
        if execution is not None:
            payload['execution'] = int(execution)
        if os_name:
            payload['os'] = os_name
        if browser:
            payload['browser'] = browser
        if keywords:
            payload['keywords'] = keywords
        if mailto:
            payload['mailto'] = mailto
        if deadline:
            payload['deadline'] = deadline
        if uid:
            payload['uid'] = uid
        if story is not None:
            payload['story'] = int(story)
        if task is not None:
            payload['task'] = int(task)
        payload.update(extra)

        # 同时传 productID 到 query string（兼容 zentao-cli 的 override 策略）
        return self._request(
            'POST', f'/products/{product_id}/bugs',
            params={'productID': product_id},
            json_data=payload,
        )

    # ── Bug 查询 / 删除 ──

    def get_bug(self, bug_id):
        self.ensure_login()
        return self._request('GET', f'/bugs/{bug_id}')

    def delete_bug(self, bug_id):
        self.ensure_login()
        return self._request('DELETE', f'/bugs/{bug_id}')

    def batch_delete_bugs(self, bug_ids):
        results = []
        for bid in bug_ids:
            try:
                results.append({'id': bid, 'ok': True, 'result': self.delete_bug(bid)})
            except Exception as e:
                results.append({'id': bid, 'ok': False, 'message': str(e)})
        return results

    # ── 附件上传（双通道） ──

    def upload_file_via_rest(self, file_path, object_type='bug', object_id=None, uid=None):
        """
        REST API v1 POST /files 上传附件。
        对应 zentao-cli 的 zentao file create 命令（API 2.0 路径，v1 兼容）。
        需要 objectType + objectID 来关联到具体 Bug。
        """
        self.ensure_login()
        fp = Path(file_path)
        if not fp.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        if uid is None:
            uid = str(uuid.uuid4())
        with open(fp, 'rb') as f:
            files = {'file': (fp.name, f)}
            data = {'objectType': object_type, 'objectID': object_id or ''}
            if uid:
                data['uid'] = uid
            try:
                result = self._request('POST', '/files', data=data, files=files)
                return {'file': str(fp), 'ok': True, 'uid': uid, 'result': result}
            except Exception as e:
                raise RuntimeError(f"REST /files 上传失败: {e}") from e

    def upload_file_via_session(self, file_path, bug_id):
        """
        通过 Session Cookie + 网页表单上传附件（兼容 ZenTao 18.x 等旧版本）。
        使用 /file-ajaxUpload-{kuid}.html 端点上传文件，然后关联到 Bug。
        """
        self.login_via_cookie()
        fp = Path(file_path)
        if not fp.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 从 Bug 详情页获取 kuid（用户标识）
        bug_page = self._request_raw('GET', f'{self.base_url}/bug-view-{bug_id}.html')
        kuid_match = re.search(r"var\s+kuid\s*=\s*['\"]([a-zA-Z0-9]+)['\"]", bug_page.text)
        if not kuid_match:
            # 尝试从产品页获取
            products_page = self._request_raw('GET', f'{self.base_url}/bug-browse-{self._get_product_from_bug(bug_id)}.html')
            kuid_match = re.search(r"var\s+kuid\s*=\s*['\"]([a-zA-Z0-9]+)['\"]", products_page.text)
        if not kuid_match:
            raise RuntimeError("无法获取用户标识 kuid，请检查登录状态")

        kuid = kuid_match.group(1)
        upload_url = f'{self.base_url}/file-ajaxUpload-{kuid}.html'

        # 尝试不同的字段名
        for field_name in ['imgFile', 'file']:
            resp = self._request_raw('POST', upload_url,
                                     data={},
                                     files={field_name: (fp.name, open(fp, 'rb'))},
                                     timeout=self.timeout)
            # 关闭文件句柄
            if hasattr(resp, 'raw') and resp.raw:
                resp.raw.release_conn()
            if resp.status_code == 200:
                try:
                    result = resp.json()
                    if result.get('result') == 'success':
                        return {'file': str(fp), 'ok': True, 'uid': None, 'result': result}
                except Exception:
                    pass
                if resp.text and 'error' not in resp.text.lower():
                    # 非 JSON 响应可能表示成功
                    return {'file': str(fp), 'ok': True, 'uid': None, 'result': resp.text}

        raise RuntimeError(f"Session 上传失败，所有字段名均不可用")

    def _get_product_from_bug(self, bug_id):
        """从 Bug 详情获取所属产品 ID。"""
        try:
            bug = self.get_bug(bug_id)
            return bug.get('product', '')
        except Exception:
            return ''

    def attach_files_to_bug(self, bug_id, file_paths):
        """
        将附件关联到已创建的 Bug。
        优先尝试 REST API /files，失败则回退到 Session Cookie 方式。
        返回 [{'file','ok','uid','message','channel'}]
        """
        self.ensure_login()
        results = []
        for fp in file_paths:
            entry = {'file': str(fp), 'ok': False, 'uid': None, 'message': '', 'channel': 'none'}
            fp = Path(fp)
            if not fp.exists():
                entry['message'] = '文件不存在'
                results.append(entry)
                continue

            # 通道 A：REST API（适用于 ZenTao 20+）
            try:
                r = self.upload_file_via_rest(str(fp), 'bug', bug_id)
                entry.update({'ok': True, 'uid': r.get('uid'), 'channel': 'rest', 'message': ''})
                results.append(entry)
                continue
            except Exception as e:
                entry['message'] = f"REST /files 失败: {e}"

            # 通道 B：Session Cookie（适用于 ZenTao 18.x 等旧版本）
            try:
                r = self.upload_file_via_session(str(fp), bug_id)
                entry.update({'ok': True, 'channel': 'session', 'message': ''})
            except Exception as e2:
                entry['message'] += f" | Session 上传失败: {e2}"

            results.append(entry)
        return results


# ──────────────────────────── CLI ────────────────────────────

def _build_client(args):
    verify = os.environ.get('ZENTAO_VERIFY_SSL', '1') != '0' and not args.no_verify
    return ZentaoClient(
        base_url=args.url,
        account=args.account,
        password=args.password,
        verify_ssl=verify,
        debug=getattr(args, 'debug', False),
    )


def _print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _read_steps_from_file(path):
    """从文件读取步骤内容，自动包装为有结构的格式。"""
    fp = Path(path)
    if not fp.exists():
        raise FileNotFoundError(f"步骤文件不存在: {fp}")
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    # 如果文件已包含【xxx】章节标记，原样使用
    if any(c in content for c in ['【', '】']):
        return content.strip()
    # 否则包装为默认结构
    return f'【测试步骤】\n{content.strip()}'


def cmd_login(args):
    client = _build_client(args)
    token = client.login()
    _print_json({'token': token})


def cmd_products(args):
    client = _build_client(args)
    client.ensure_login()
    _print_json(client.get_products(limit=args.limit))


def cmd_modules(args):
    client = _build_client(args)
    client.ensure_login()
    _print_json(client.get_modules(args.product_id, module_type=args.module_type))


def cmd_builds(args):
    client = _build_client(args)
    client.ensure_login()
    _print_json(client.get_builds(
        product_id=args.product_id,
        project_id=args.project_id,
        limit=args.limit,
    ))


def cmd_users(args):
    client = _build_client(args)
    client.ensure_login()
    _print_json(client.get_users(limit=args.limit))


def cmd_delete_bug(args):
    client = _build_client(args)
    client.ensure_login()
    _print_json(client.delete_bug(args.bug_id))


def cmd_batch_delete_bugs(args):
    client = _build_client(args)
    client.ensure_login()
    _print_json(client.batch_delete_bugs(args.bug_ids))


def cmd_attach(args):
    client = _build_client(args)
    client.ensure_login()
    results = client.attach_files_to_bug(args.object_id, args.files)
    ok = sum(1 for r in results if r['ok'])
    print(f"[附件] 成功 {ok}/{len(results)}", file=sys.stderr)
    _print_json(results)


def cmd_upload(args):
    client = _build_client(args)
    client.ensure_login()
    result = client.upload_file_via_rest(args.file, 'bug', args.object_id)
    _print_json({'result': result})


def cmd_create_bug(args):
    client = _build_client(args)
    client.ensure_login()

    # 处理步骤内容（支持多行文件输入）
    steps = None
    if args.steps:
        steps = args.steps
    if args.steps_file:
        steps = _read_steps_from_file(args.steps_file)

    if not steps:
        raise ValueError('必须通过 --steps 或 --steps-file 提供步骤内容')

    # 转换为 ZenTao HTML 格式（多行换行支持）
    steps_html = ZentaoClient.steps_to_html(steps)

    result = client.create_bug(
        product_id=args.product_id,
        title=args.title,
        severity=args.severity,
        pri=args.pri,
        opened_build=args.opened_build,
        steps=steps_html,
        module=args.module,
        assigned_to=args.assigned_to,
        bug_type=args.bug_type,
        project=args.project,
        execution=args.execution,
        os_name=args.os,
        browser=args.browser,
        keywords=args.keywords,
        mailto=args.mailto,
        deadline=args.deadline,
        uid=args.uid,
    )
    _print_json(result)


def cmd_upload_files(args):
    """上传附件并关联到已存在的 Bug（REST + Session 双通道）。"""
    client = _build_client(args)
    client.ensure_login()
    results = client.attach_files_to_bug(args.object_id, args.files)
    ok = sum(1 for r in results if r['ok'])
    print(f"[附件] 成功 {ok}/{len(results)}", file=sys.stderr)
    _print_json({'results': results})


def main():
    parser = argparse.ArgumentParser(description='禅道 Bug 提交工具')
    parser.add_argument('--url', default=os.environ.get('ZENTAO_URL', ''),
                        help='禅道根地址（默认读环境变量 ZENTAO_URL）')
    parser.add_argument('--account', default=os.environ.get('ZENTAO_ACCOUNT', ''),
                        help='登录账号')
    parser.add_argument('--password', default=os.environ.get('ZENTAO_PASSWORD', ''),
                        help='登录密码')
    parser.add_argument('--no-verify', action='store_true',
                        help='不校验 SSL 证书（内网自签名证书时使用）')
    parser.add_argument('--debug', action='store_true',
                        help='打印请求和响应详情')

    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('login', help='登录获取 token').set_defaults(func=cmd_login)

    p = sub.add_parser('products', help='获取产品列表')
    p.add_argument('--limit', type=int, default=100)
    p.set_defaults(func=cmd_products)

    p = sub.add_parser('modules', help='获取产品模块列表')
    p.add_argument('--product-id', type=int, required=True)
    p.add_argument('--module-type', default='bug', help='模块类型: bug/case/task/story')
    p.set_defaults(func=cmd_modules)

    p = sub.add_parser('builds', help='获取版本列表')
    p.add_argument('--product-id', type=int, default=None)
    p.add_argument('--project-id', type=int, default=None)
    p.add_argument('--limit', type=int, default=100)
    p.set_defaults(func=cmd_builds)

    p = sub.add_parser('users', help='获取用户列表')
    p.add_argument('--limit', type=int, default=200)
    p.set_defaults(func=cmd_users)

    p = sub.add_parser('delete-bug', help='删除单条 Bug')
    p.add_argument('--bug-id', type=int, required=True)
    p.set_defaults(func=cmd_delete_bug)

    p = sub.add_parser('batch-delete-bugs', help='批量删除 Bug')
    p.add_argument('--bug-ids', nargs='+', type=int, required=True)
    p.set_defaults(func=cmd_batch_delete_bugs)

    p = sub.add_parser('create-bug', help='创建 Bug（支持多行步骤和附件）')
    p.add_argument('--product-id', type=int, required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--severity', type=int, required=True, help='严重程度 1-5')
    p.add_argument('--pri', type=int, required=True, help='优先级 1-5')
    p.add_argument('--opened-build', required=True, nargs='+',
                   help='影响版本 ID（支持字符串如 APP_601_28）')
    p.add_argument('--steps', default=None, help='重现步骤（plain text，\\n 分隔）')
    p.add_argument('--steps-file', default=None,
                   help='从文件读取步骤内容（支持多行，含【xxx】标记则原样使用）')
    p.add_argument('--module', type=int, default=None)
    p.add_argument('--assigned-to', default=None, help='指派给用户账号')
    p.add_argument('--bug-type', default='codeerror', help='Bug 类型')
    p.add_argument('--project', type=int, default=None)
    p.add_argument('--execution', type=int, default=None)
    p.add_argument('--os', default=None, help='操作系统')
    p.add_argument('--browser', default=None, help='浏览器')
    p.add_argument('--keywords', default=None)
    p.add_argument('--mailto', default=None)
    p.add_argument('--deadline', default=None)
    p.add_argument('--uid', default=None, help='附件关联标识')
    p.set_defaults(func=cmd_create_bug)

    p = sub.add_parser('upload-files', help='上传附件并关联到已存在的 Bug（双通道）')
    p.add_argument('--object-id', type=int, required=True, help='Bug ID')
    p.add_argument('--files', nargs='+', required=True, help='附件文件路径')
    p.set_defaults(func=cmd_upload_files)

    p = sub.add_parser('attach', help='上传附件并关联到对象')
    p.add_argument('--object-type', required=True, help='对象类型，如 bug')
    p.add_argument('--object-id', type=int, required=True, help='对象 ID')
    p.add_argument('--files', nargs='+', required=True, help='附件文件路径')
    p.set_defaults(func=cmd_attach)

    p = sub.add_parser('upload', help='上传附件（REST /files）')
    p.add_argument('--file', required=True)
    p.add_argument('--object-id', type=int, default=None)
    p.add_argument('--uid', default=None)
    p.set_defaults(func=cmd_upload)

    args = parser.parse_args()
    if not args.url or not args.account or not args.password:
        parser.error('必须通过 --url/--account/--password 或环境变量 ZENTAO_URL/ZENTAO_ACCOUNT/ZENTAO_PASSWORD 提供连接信息')

    try:
        args.func(args)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
