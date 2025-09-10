from flask import Flask, request, render_template_string
import requests, json
from bs4 import BeautifulSoup

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>WKBL URL 생성기</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .card { border-radius: 1rem; }
        .copy-btn { min-width: 80px; }
        #url_textarea { resize: none; }
        @media (max-width: 576px) {
            .copy-btn { width: 100%; margin-top: 0.5rem; }
        }
        /* Toast 위치 */
        #toast-container {
            position: fixed;
            bottom: 1rem;
            right: 1rem;
            z-index: 1055;
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
                        
                        <!-- 로그인 폼 -->
                        <form method="post" class="mb-4">
                            <div class="mb-3">
                                <label class="form-label">아이디</label>
                                <input type="text" class="form-control" name="user_id" placeholder="아이디 입력" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">비밀번호</label>
                                <input type="password" class="form-control" name="user_pwd" placeholder="비밀번호 입력" required>
                            </div>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary btn-lg">생성</button>
                            </div>
                        </form>

                        <!-- 결과 영역 -->
                        {% if final_url %}
                        <div class="mb-3">
                            <label class="form-label">생성된 URL</label>
                            <textarea id="url_textarea" class="form-control mb-2" rows="3" readonly>{{ final_url }}</textarea>
                            <button class="btn btn-outline-secondary copy-btn" onclick="copyURL()">복사</button>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast 컨테이너 -->
    <div id="toast-container"></div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
    function copyURL() {
        const textarea = document.getElementById('url_textarea');
        textarea.select();
        textarea.setSelectionRange(0, 99999); // 모바일용
        try {
            if (document.execCommand('copy')) {
                showToast("URL이 클립보드에 복사되었습니다!");
            } else {
                showToast("복사 실패");
            }
        } catch (err) {
            showToast("복사 중 오류 발생");
        }
    }

    function showToast(message) {
        // Toast HTML 생성
        const toastEl = document.createElement("div");
        toastEl.className = "toast align-items-center text-bg-primary border-0";
        toastEl.setAttribute("role", "alert");
        toastEl.setAttribute("aria-live", "assertive");
        toastEl.setAttribute("aria-atomic", "true");
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        document.getElementById("toast-container").appendChild(toastEl);

        // Bootstrap Toast 초기화 및 자동 표시
        const bsToast = new bootstrap.Toast(toastEl, { delay: 2000 });
        bsToast.show();

        // 2초 후 DOM에서 제거
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    final_url = None
    if request.method == "POST":
        user_id = request.form["user_id"]
        user_pwd = request.form["user_pwd"]

        session_requests = requests.Session()
        login_url = "https://www.wkbl.or.kr/member/login/login_v2_proc.asp"
        payload = {"moveurl": "", "user_id": user_id, "user_pwd": user_pwd}
        resp = session_requests.post(login_url, data=payload)
        if "비밀번호가 일치하지 않습니다. " in resp.text:
            final_url = "로그인 실패"
        else:
            ticket_url = "https://www.wkbl.or.kr/ticket/ticketing.asp"
            resp = session_requests.get(ticket_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            el = soup.select_one(".btn_my_reserve")
            if el:
                obj = json.loads(el.get("data-obj"))
                final_url = f"https://facility.ticketlink.co.kr/facility/direct/member/reserve?partnerNo={obj['partnerNo']}&memberIdEnc={obj['memberIdEnc']}"
            else:
                final_url = "계정 정보가 틀렸습니다."
    return render_template_string(HTML_TEMPLATE, final_url=final_url)

if __name__ == "__main__":
    app.run(debug=True)
