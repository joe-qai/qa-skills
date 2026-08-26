#!/usr/bin/env python3
"""
禅道 (ZenTao) REST API v1 客户端 —— 自动提交 Bug

支持：账号密码登录换 token、获取产品/模块/版本/用户列表、上传附件、创建 Bug。
既可作为 Python 模块 import，也可作为 CLI 工具直接调用。

用法示例（CLI，连接信息优先从环境变量 ZENTAO_URL/ZENTAO_ACCOUNT/ZENTAO_PASSWORD 读取）：
  # 登录并获取 token
  python3 zentao_client.py login

  # 获取产品列表
  python3 zentao_client.py products --url ... --account ... --password ...

  # 获取某产品的 Bug 模块
  python3 zentao_client.py modules --product-id 1 --url ... --account ... --password ...

  # 获取版本列表
  python3 zentao_client.py builds --product-id 1 --url ... --account ... --password ...

  # 获取用户列表
  python3 zentao_client.py users --url ... --account ... --password ...

  # 上传附件
  python3 zentao_client.py upload --file /path/to/screenshot.png --uid my-uid-001 --url ... --account ... --password ...

  # 创建 Bug（最简）
  python3 zentao_client.py create-bug \
    --product-id 1 --title "登录页面崩溃" --severity 2 --pri 2 \
    --opened-build 3 --steps "1.打开登录页\n2.点击登录\n3.页面崩溃" \
    --url ... --account ... --password ...

  # 创建 Bug（带附件和完整字段）
  python3 zentao_client.py create-bug \
    --product-id 1 --module 5 --title "xxx" --severity 3 --pri 3 \
    --opened-build 3 --assigned-to zhangsan \
    --steps "【测试步骤】\n  1. xxx\n\n【实际结果】\n  xxx\n\n【预期结果】\n  xxx" \
    --uid my-uid-001 --os "Windows 11" --browser "Chrome 120" \
    --url ... --account ... --password ...

环境变量（可替代命令行参数）：
  ZENTAO_URL, ZENTAO_ACCOUNT, ZENTAO_PASSWORD, ZENTAO_VERIFY_SSL (0/1)
"""

import os
import sys
import json
import uuid
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("错误：缺少 requests 库，请运行 pip3 install requests", file=sys.stderr)
    sys.exit(1)


# ──────────────────────────── 客户端类 ────────────────────────────

class ZentaoClient:
    """禅道 REST API v1 客户端。"""

    def __init__(self, base_url, account, password, verify_ssl=True, debug=False):
        """
        base_url: 禅道根地址，如 https://<host>/zentao
        account/password: 登录账号密码
        verify_ssl: 是否校验 SSL 证书（内网自签名证书可设 False）
        debug: 开启后打印请求和响应详情，便于排查
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = self.base_url + '/api.php/v1'
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
        """发送带 token 的请求，返回解析后的 JSON（或原始文本）。"""
        url = self.api_base + path
        req_headers = {}
        if headers:
            req_headers.update(headers)
        if self.token:
            req_headers['Token'] = self.token
        # 上传文件时不要覆盖 Content-Type，让 requests 自动设置 boundary
        if files:
            req_headers.pop('Content-Type', None)

        if self.debug:
            print(f"[DEBUG] {method} {url}", file=sys.stderr)
            if params:
                print(f"[DEBUG] params: {params}", file=sys.stderr)
            if json_data:
                print(f"[DEBUG] body: {json.dumps(json_data, ensure_ascii=False)[:500]}", file=sys.stderr)
            if data and not files:
                print(f"[DEBUG] data: {data}", file=sys.stderr)
            print(f"[DEBUG] headers: {req_headers}", file=sys.stderr)

        resp = self.session.request(
            method, url,
            params=params,
            json=json_data,
            data=data,
            files=files,
            headers=req_headers or None,
            verify=self.verify_ssl,
            timeout=30,
        )

        if self.debug:
            print(f"[DEBUG] response status: {resp.status_code}", file=sys.stderr)
            print(f"[DEBUG] response body: {resp.text[:1000]}", file=sys.stderr)

        return self._parse_response(resp)

    @staticmethod
    def _parse_response(resp):
        """统一解析响应，出错时抛出带上下文的异常。"""
        try:
            body = resp.json()
        except ValueError:
            body = resp.text

        if resp.status_code >= 400:
            raise RuntimeError(
                f"HTTP {resp.status_code} {resp.reason} | URL: {resp.url} | "
                f"Response: {json.dumps(body, ensure_ascii=False)[:500]}"
            )
        # 禅道部分接口在 body 中返回错误
        if isinstance(body, dict) and body.get('error'):
            raise RuntimeError(f"禅道接口错误: {json.dumps(body, ensure_ascii=False)[:500]}")
        return body

    # ── 认证 ──

    def login(self):
        """POST /tokens 用账号密码换取 token，返回 token 字符串。"""
        resp = self.session.post(
            self.api_base + '/tokens',
            json={'account': self.account, 'password': self.password},
            verify=self.verify_ssl,
            timeout=30,
        )
        body = self._parse_response(resp)
        self.token = body.get('token')
        if not self.token:
            raise RuntimeError(f"登录失败，未返回 token: {json.dumps(body, ensure_ascii=False)[:500]}")
        return self.token

    def ensure_login(self):
        """确保已登录，未登录则自动登录。"""
        if not self.token:
            self.login()
        return self.token

    # ── 产品 ──

    def get_products(self, limit=100):
        """GET /products 获取产品列表。"""
        self.ensure_login()
        return self._request('GET', '/products', params={'limit': limit})

    # ── 模块 ──

    def get_modules(self, product_id, module_type='bug'):
        """
        GET /modules?type=<type>&id=<product_id> 获取产品模块树。
        module_type: bug / case / task / story 等
        """
        self.ensure_login()
        return self._request('GET', f'/modules?type={module_type}&id={product_id}')

    # ── 版本 (Build) ──

    def get_builds(self, product_id=None, project_id=None, limit=100):
        """
        GET /builds 获取版本列表。
        优先按产品维度查询（type=product&param=<pid>），也可按项目查询。
        """
        self.ensure_login()
        params = {'limit': limit}
        if product_id:
            params['type'] = 'product'
            params['param'] = product_id
        elif project_id:
            params['project'] = project_id
        return self._request('GET', '/builds', params=params)

    def get_execution(self, product_id, limit=20):
        """GET /executions?product=<id> 获取产品执行列表，返回第一个执行ID。"""
        self.ensure_login()
        r = self._request('GET', '/executions', params={'product': product_id, 'limit': limit})
        executions = r.get('executions', [])
        if executions:
            return executions[0]['id']
        return None

    def fuzzy_match_build(self, product_id, build_name, limit=100):
        """
        从产品已有Bug中提取openedBuild，对输入的build_name做模糊匹配。
        返回匹配到的build名，无匹配则返回原值。
        """
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
        # 精确匹配
        if build_name in builds:
            return build_name
        # 模糊匹配：输入是已有版本的子串，或已有版本包含输入
        candidates = []
        for b in builds:
            if build_name in b or b in build_name:
                candidates.append(b)
        if candidates:
            return candidates[0]
        return build_name

    # ── 用户 ──

    def get_users(self, limit=200):
        """GET /users 获取用户列表（含 account 和 realname）。"""
        self.ensure_login()
        return self._request('GET', '/users', params={'limit': limit})

    # ── 附件上传（纯 REST API，两步法第二步） ──

    def upload_file(self, file_path, uid=None, field_name='file'):
        """
        POST /files 上传附件（REST API），返回 {id, url, ...}。
        uid: 关联标识。创建 Bug 时传入相同 uid 即可自动关联附件。
             不传则自动生成 UUID。
        field_name: 上传文件字段名，默认 'file'。部分禅道版本用 'imgFile'，
                    可传 field_name='imgFile' 尝试。

        注意：部分禅道实例（尤其企业版/老版本）的 /api.php/v1/files 接口存在
        服务端问题，始终返回 {"error":"error"}。此时请使用 upload_attachment
        走 /attachments 通道（objectType/objectID）上传并关联到已创建的 Bug。
        """
        self.ensure_login()
        if uid is None:
            uid = str(uuid.uuid4())
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        with open(file_path, 'rb') as f:
            files = {field_name: (file_path.name, f)}
            data = {'uid': uid}
            return self._request('POST', '/files', data=data, files=files), uid

    def upload_files(self, file_paths, uid=None):
        """批量上传附件（REST /files），共用同一个 uid。返回 (results, uid)。"""
        if uid is None:
            uid = str(uuid.uuid4())
        results = []
        for fp in file_paths:
            result, _ = self.upload_file(fp, uid=uid)
            results.append(result)
        return results, uid

    def upload_attachment(self, object_type, object_id, file_path):
        """
        POST /attachments 上传附件并直接关联到已创建的对象（Bug/用例等）。
        两步法第二步：先建单，再上传附件关联，附件不能和建单一次性提交。
        data: objectType=bug, objectID=<bug_id>，multipart/form-data，不带 JSON 头。
        """
        self.ensure_login()
        fp = Path(file_path)
        if not fp.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        with open(fp, 'rb') as f:
            files = {'file': (fp.name, f)}
            data = {'objectType': object_type, 'objectID': object_id}
            return self._request('POST', '/attachments', data=data, files=files)

    def attach_files_to_object(self, object_type, object_id, file_paths):
        """
        两步法第二步：把本地附件关联到已创建的 Bug/对象。
        纯 REST API 通道：
          通道 A：POST /files（uid）上传
          通道 B：POST /attachments（objectType/objectID）上传并关联
        返回 [{'file','ok','id','message','channel'}]
        """
        self.ensure_login()
        results = []
        uid = str(uuid.uuid4())
        for fp in file_paths:
            entry = {'file': str(fp), 'ok': False, 'id': None, 'message': [], 'channel': 'none'}
            fp = Path(fp)
            if not fp.exists():
                entry['message'] = '文件不存在'
                results.append(entry)
                continue
            # 通道 A：REST /files（带 uid）
            try:
                result, _ = self.upload_file(str(fp), uid=uid)
                entry['ok'] = True
                entry['id'] = result.get('id', result.get('fileID'))
                entry['channel'] = 'rest'
            except Exception as e:
                entry['message'].append(f"REST /files 失败: {e}")
            # 通道 B：/attachments（objectType/objectID），仅对通道 A 失败的文件重试
            if not entry['ok']:
                try:
                    resp = self._post_attachment(object_type, object_id, str(fp))
                    entry.update({'ok': True, 'id': resp.get('id'), 'channel': 'attachments', 'message': []})
                except Exception as e:
                    entry['message'].append(f"/attachments 失败: {e}")
            if isinstance(entry['message'], list):
                entry['message'] = ' | '.join(entry['message'])
            results.append(entry)
        return results

    def _post_attachment(self, object_type, object_id, file_path):
        """POST /attachments（multipart，objectType/objectID），上传并关联到对象。"""
        fp = Path(file_path)
        with open(fp, 'rb') as f:
            files = {'file': (fp.name, f)}
            data = {'objectType': object_type, 'objectID': object_id}
            resp = self._request('POST', '/attachments', data=data, files=files)
        return resp if isinstance(resp, dict) else {}

    def create_bug(self, product_id, title, severity, pri, opened_build,
                   steps, module=None, assigned_to=None, bug_type='codeerror',
                   project=None, execution=None, os_name=None, browser=None,
                   keywords=None, mailto=None, deadline=None, uid=None,
                   story=None, task=None, **extra):
        """
        POST /products/<product_id>/bugs 创建 Bug。

        必填: product_id, title, severity, pri, opened_build, steps
        选填: module, assigned_to, bug_type, project, execution, os_name,
              browser, keywords, mailto, deadline, uid(关联附件), story, task

        opened_build: 版本 ID，int 或 int 列表。
        steps: 重现步骤 HTML 字符串，如 "<p>1. xxx</p><p>预期: xxx</p>"
        severity: 1-5 (1最严重)
        pri: 1-5 (1最高优先级)
        bug_type: codeerror/config/install/security/performance/standard/
                  automation/designdefect/others
        """
        self.ensure_login()
        # 将 opened_build 规范化为列表
        if isinstance(opened_build, (int, str)):
            opened_build = [opened_build]
        # 模糊匹配版本名（用已有 Bug 的版本列表）
        resolved = []
        for b in opened_build:
            s = str(b)
            matched = self.fuzzy_match_build(product_id, s)
            try:
                resolved.append(int(matched))
            except ValueError:
                resolved.append(matched)
        opened_build = resolved
        # 自动注入 execution（如未指定；查询失败不阻断建单）
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

        return self._request('POST', f'/products/{product_id}/bugs', json_data=payload)

    # ── 查询 Bug（辅助） ──

    def get_bug(self, bug_id):
        """GET /bugs/<id> 获取 Bug 详情。"""
        self.ensure_login()
        return self._request('GET', f'/bugs/{bug_id}')

    # ── 删除 Bug ──

    def delete_bug(self, bug_id):
        """DELETE /bugs/<id> 删除单条 Bug。"""
        self.ensure_login()
        return self._request('DELETE', f'/bugs/{bug_id}')

    def batch_delete_bugs(self, bug_ids):
        """批量删除 Bug：禅道无原生批量删除接口，循环调用单删。"""
        results = []
        for bid in bug_ids:
            try:
                results.append({'id': bid, 'ok': True, 'result': self.delete_bug(bid)})
            except Exception as e:
                results.append({'id': bid, 'ok': False, 'message': str(e)})
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


def _steps_to_html(steps):
    """
    直接返回纯文本步骤。

    注意：部分禅道实例会在服务端对 steps 内容做 HTML 转义，若客户端预先把
    \\n 转成 <br />，会被二次转义成 &lt;br /&gt; 导致页面显示字面量标签。
    实测服务端会保留 \\n 并自行处理换行，因此客户端不做任何转换。
    """
    return steps


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
    results = client.attach_files_to_object(args.object_type, args.object_id, args.files)
    ok = sum(1 for r in results if r['ok'])
    print(f"[附件] 成功 {ok}/{len(results)}", file=sys.stderr)
    _print_json(results)


def cmd_upload(args):
    client = _build_client(args)
    client.ensure_login()
    field_name = getattr(args, 'field_name', 'file')
    result, uid = client.upload_file(args.file, uid=args.uid, field_name=field_name)
    _print_json({'uid': uid, 'result': result})


def cmd_create_bug(args):
    client = _build_client(args)
    client.ensure_login()

    result = client.create_bug(
        product_id=args.product_id,
        title=args.title,
        severity=args.severity,
        pri=args.pri,
        opened_build=args.opened_build,
        steps=_steps_to_html(args.steps),
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


def main():
    parser = argparse.ArgumentParser(description='禅道 REST API v1 客户端')
    parser.add_argument('--url', default=os.environ.get('ZENTAO_URL', ''),
                        help='禅道根地址，如 https://<host>/zentao（默认读环境变量 ZENTAO_URL）')
    parser.add_argument('--account', default=os.environ.get('ZENTAO_ACCOUNT', ''),
                        help='登录账号')
    parser.add_argument('--password', default=os.environ.get('ZENTAO_PASSWORD', ''),
                        help='登录密码')
    parser.add_argument('--no-verify', action='store_true',
                        help='不校验 SSL 证书（内网自签名证书时使用）')
    parser.add_argument('--debug', action='store_true',
                        help='打印请求和响应详情，便于排查问题')

    sub = parser.add_subparsers(dest='command', required=True)

    # login
    sub.add_parser('login', help='登录获取 token').set_defaults(func=cmd_login)

    # products
    p = sub.add_parser('products', help='获取产品列表')
    p.add_argument('--limit', type=int, default=100)
    p.set_defaults(func=cmd_products)

    # modules
    p = sub.add_parser('modules', help='获取产品模块列表')
    p.add_argument('--product-id', type=int, required=True)
    p.add_argument('--module-type', default='bug', help='模块类型: bug/case/task/story')
    p.set_defaults(func=cmd_modules)

    # builds
    p = sub.add_parser('builds', help='获取版本列表')
    p.add_argument('--product-id', type=int, default=None)
    p.add_argument('--project-id', type=int, default=None)
    p.add_argument('--limit', type=int, default=100)
    p.set_defaults(func=cmd_builds)

    # users
    p = sub.add_parser('users', help='获取用户列表')
    p.add_argument('--limit', type=int, default=200)
    p.set_defaults(func=cmd_users)

    # upload
    p = sub.add_parser('upload', help='上传附件（两步法准备）')
    p.add_argument('--file', required=True)
    p.add_argument('--uid', default=None, help='关联标识，不传自动生成')
    p.add_argument('--field-name', default='file',
                   help='上传文件字段名，默认 file，部分版本用 imgFile')
    p.set_defaults(func=cmd_upload)

    # create-bug
    p = sub.add_parser('create-bug', help='创建 Bug（第一步：只建单，不含附件）')
    p.add_argument('--product-id', type=int, required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--severity', type=int, required=True, help='严重程度 1-5')
    p.add_argument('--pri', type=int, required=True, help='优先级 1-5')
    p.add_argument('--opened-build', required=True, nargs='+',
                   help='影响版本 ID，可多个（支持字符串如 APP_601_28）')
    p.add_argument('--steps', required=True, help='重现步骤（plain text，\\n 分隔，服务端处理换行）')
    p.add_argument('--module', type=int, default=None)
    p.add_argument('--assigned-to', default=None, help='指派给用户账号')
    p.add_argument('--bug-type', default='codeerror',
                   help='Bug 类型: codeerror/config/install/security/...')
    p.add_argument('--project', type=int, default=None)
    p.add_argument('--execution', type=int, default=None)
    p.add_argument('--os', default=None)
    p.add_argument('--browser', default=None)
    p.add_argument('--keywords', default=None)
    p.add_argument('--mailto', default=None)
    p.add_argument('--deadline', default=None)
    p.add_argument('--uid', default=None, help='附件关联标识（与 attach 一致）')
    p.set_defaults(func=cmd_create_bug)

    # delete-bug
    p = sub.add_parser('delete-bug', help='删除单条 Bug')
    p.add_argument('--bug-id', type=int, required=True)
    p.set_defaults(func=cmd_delete_bug)

    # batch-delete-bugs
    p = sub.add_parser('batch-delete-bugs', help='批量删除 Bug')
    p.add_argument('--bug-ids', nargs='+', type=int, required=True)
    p.set_defaults(func=cmd_batch_delete_bugs)

    # attach（两步法第二步：附件关联到已创建的 Bug/对象）
    p = sub.add_parser('attach', help='上传附件并关联到已存在的对象(bug/case 等)')
    p.add_argument('--object-type', required=True, help='对象类型，如 bug')
    p.add_argument('--object-id', type=int, required=True, help='对象 ID（如 bug_id）')
    p.add_argument('--files', nargs='+', required=True, help='附件文件路径')
    p.set_defaults(func=cmd_attach)

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
