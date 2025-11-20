from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, xmltodict, os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
load_dotenv()

DART_KEY = os.getenv("DART_API_KEY")

# ----------------------------------------
# 🔹 DART API 호출 (v3: fnlttMultiAcnt.xml)
# ----------------------------------------
def fetch_dart_data(corp_code, bsns_year, reprt_code="11013"):
    url = "https://opendart.fss.or.kr/api/fnlttMultiAcnt.xml"
    params = {
        "crtfc_key": DART_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code
    }
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return None
    return xmltodict.parse(res.text)

# ----------------------------------------
# 🔹 주요 항목 추출
# ----------------------------------------
def extract_financials(data):
    try:
        items = data.get("result", {}).get("list", [])
        f = {}
        for item in items:
            name = item.get("account_nm")
            if not name:
                continue
            th = item.get("thstrm_amount", "0").replace(",", "")
            f[name.strip()] = float(th) if th.isdigit() else 0
        return f
    except Exception as e:
        return {}

# ----------------------------------------
# 🔹 비율 계산
# ----------------------------------------
def calculate_ratios(f):
    try:
        ratios = {
            "영업이익률": round(f.get("영업이익", 0) / f.get("매출액", 1) * 100, 2),
            "순이익률": round(f.get("당기순이익", 0) / f.get("매출액", 1) * 100, 2),
            "부채비율": round(f.get("부채총계", 0) / f.get("자본총계", 1) * 100, 2),
            "ROE": round(f.get("당기순이익", 0) / f.get("자본총계", 1) * 100, 2)
        }
        return ratios
    except:
        return {"error": "비율 계산 실패"}

# ----------------------------------------
# 🧩 /ratios - 주요 재무비율 반환
# ----------------------------------------
@app.route("/ratios")
def get_ratios():
    corp_code = request.args.get("corp_code")
    bsns_year = request.args.get("bsns_year")
    reprt_code = request.args.get("reprt_code", "11013")

    if not corp_code or not bsns_year:
        return jsonify({"error": "Missing par
