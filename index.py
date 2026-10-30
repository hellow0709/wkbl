
from flask import Flask, request, render_template_string
from urllib.parse import urlencode
import requests
import json
from bs4 import BeautifulSoup

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>WKBL URL 생성기</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .card { border-radius: 1rem; }
        .copy-btn { min-width: 80px; }
        #url_textarea { resize: none; overflow-wrap: anywhere; }
        #toast-container {
            position: fixed;
            bottom: 1rem;
            right: 1rem;
            z-index: 1055;
        }
        @media (max-width: 576px) {
            .copy-btn { width: 100%; margin-top: 0.5rem; }
        }
    </style>
</head>
<body>
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-md-6 col-sm-10">
            <div class="card shadow-sm">
                <div class="card-body p-4">
                    <h3 class="card-title text-center mb-4">WKBL URL 생성기</h3>

                    <form method="post" class="mb-4">
                        <div class="mb-3">
                            <label class="form-label">아이디</label>
                            <input type="text" class="form-control"
                                   name="user_id" placeholder="아이디 입력" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">비밀번호</label>
                            <input type="password" class="form-control"
                                   name="user_pwd" placeholder="비밀번호 입력" required>
                        </div>
                        <div class="d-grid">
                            <button type="submit" class="btn btn-primary btn-lg">생성</button>
                        </div>
                    </form>

                    {% if error %}
                    <div class="alert alert-danger" role="alert">
                        {{ error }}
                    </div>
                    {% endif %}

                    {% if final_url %}
                    <div class="mb-3">
                        <label class="form-label">생성된 URL</label>
                        <textarea id="url_textarea" class="form-control mb-2"
                                  rows="4" readonly>{{ final_url }}</textarea>
                        <button class="btn btn-outline-secondary copy-btn"
                                onclick="copyURL()">복사</button>
                        <a href="{{ final_url }}" target="_blank"
                           rel="noopener noreferrer"
                           class="btn btn-outline-primary ms-2">접속</a>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>

<div id="toast-container"></div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
async function copyURL() {
    const textarea = document.getElementById('url_textarea');
    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(textarea.value);
        } else {
            textarea.select();
            textarea.setSelectionRange(0, 99999);
            if (!document.execCommand('copy')) {
                throw new Error('복사 실패');
            }
        }
        showToast("URL이 클립보드에 복사되었습니다!");
    } catch (err) {
        showToast("복사 중 오류 발생");
    }
}

function showToast(message) {
    const toastEl = document.createElement("div");
    toastEl.className = "toast align-items-center text-bg-primary border-0";
    toastEl.setAttribute("role", "alert");
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body"></div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto"
                    data-bs-dismiss="toast"></button>
        </div>`;
    toastEl.querySelector(".toast-body").textContent = message;
    document.getElementById("toast-container").appendChild(toastEl);
    new bootstrap.Toast(toastEl, { delay: 2000 }).show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}
</script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    final_url = None
    error = None

    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        user_pwd = request.form.get("user_pwd", "")

        if not user_id or not user_pwd:
            error = "아이디와 비밀번호를 입력해주세요."
        else:
            try:
                with requests.Session() as session:
                    login_url = (
                        "https://www.wkbl.or.kr/member/login/login_v2_proc.asp"
                    )

                    payload = {
                        "moveurl": "",
                        "user_id": user_id,
                        "user_pwd": user_pwd
                    }

                    resp = session.post(
                        login_url,
                        data=payload,
                        timeout=15
                    )
                    resp.raise_for_status()

                    if "비밀번호가 일치하지 않습니다" in resp.text:
                        error = "로그인 실패: 비밀번호를 확인해주세요."
                    else:
                        ticket_url = (
                            "https://www.wkbl.or.kr/ticket/ticketing.asp"
                        )

                        resp = session.get(ticket_url, timeout=15)
                        resp.raise_for_status()

                        soup = BeautifulSoup(resp.text, "html.parser")
                        el = soup.select_one(".btn_my_reserve")

                        if not el:
                            error = "예약 버튼을 찾지 못했습니다. 로그인 상태나 사이트 구조를 확인해주세요."
                        else:
                            raw_data = el.get("data-obj")

                            if not raw_data:
                                error = "예약 버튼에 계정 정보가 없습니다."
                            else:
                                obj = json.loads(raw_data)

                                partner_no = obj.get("partnerNo")
                                member_id_enc = obj.get("memberIdEnc")

                                if not partner_no or not member_id_enc:
                                    error = "partnerNo 또는 memberIdEnc 값이 없습니다."
                                else:
                                    params = {
                                        "partnerNo": partner_no,
                                        "memberIdEnc": member_id_enc
                                    }

                                    base_url = (
                                        "https://facility.ticketlink.co.kr"
                                        "/facility/direct/member/reserve"
                                    )

                                    final_url = base_url + "?" + urlencode(params)

            except requests.RequestException as exc:
                app.logger.warning("WKBL 요청 실패: %s", type(exc).__name__)
                error = "WKBL 서버 통신에 실패했습니다."
            except (ValueError, TypeError, KeyError):
                error = "WKBL 예약 정보를 해석하지 못했습니다."

    return render_template_string(
        HTML_TEMPLATE,
        final_url=final_url,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)
