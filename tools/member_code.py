"""위원 코드 만들기: 성명 영문 이니셜 3자 + 휴대전화 뒷자리 4개 (예: 박근호, 3185 -> PKH3185)

사용: python3 tools/member_code.py 유인호 0881
      python3 tools/member_code.py --test   (지금까지 발급한 코드와 규칙이 맞는지 확인)

규칙
- 성씨 예외: 박 P, 조 C, 이 L, 임 L, 림 L, 리 L (흔히 쓰는 영문 표기 Park, Cho, Lee, Lim)
- 그 밖의 글자는 첫소리(초성) 기준: ㄱ K ㄲ K ㄴ N ㄷ D ㄸ D ㄹ R ㅁ M ㅂ B ㅃ B ㅅ S ㅆ S ㅈ J ㅉ J ㅊ C ㅋ K ㅌ T ㅍ P ㅎ H
- 첫소리가 ㅇ 이면 모음으로: ㅏ ㅐ A, ㅑ ㅒ ㅕ ㅖ ㅛ ㅠ Y, ㅓ ㅔ ㅡ ㅢ E, ㅗ ㅚ O, ㅘ ㅙ ㅜ ㅝ ㅞ ㅟ W, ㅣ I
  (예: 안 A, 양 Y, 영 Y, 윤 Y, 유 Y, 용 Y, 은 E, 인 I)
"""
import sys

CHO = "KKNDDRMBBSS-JJCKTPH"          # 초성 19자 순서 (ㅇ 은 '-')
JUNG_O = "AAYYEEYYOWWOYWWWWYEEI"     # ㅇ 뒤 중성 21자 순서
SURNAME = {"박": "P", "조": "C", "이": "L", "임": "L", "림": "L", "리": "L"}


def initial(ch, first=False):
    if first and ch in SURNAME:
        return SURNAME[ch]
    n = ord(ch) - 0xAC00
    if not 0 <= n < 11172:
        raise ValueError("한글 음절이 아닙니다: " + ch)
    cho, jung = n // 588, (n % 588) // 28
    c = CHO[cho]
    return JUNG_O[jung] if c == "-" else c


def member_code(name, last4):
    name = name.replace(" ", "")
    digits = "".join(d for d in str(last4) if d.isdigit())[-4:]
    if len(digits) != 4:
        raise ValueError("휴대전화 뒷자리 4개가 필요합니다")
    return "".join(initial(ch, i == 0) for i, ch in enumerate(name)) + digits


ISSUED = {  # 지금까지 발급한 코드 (사이트 · 시트 · 아임웹 쿠폰과 같아야 함)
    ("박근호", "3185"): "PKH3185", ("조성희", "7321"): "CSH7321", ("지정인", "0046"): "JJI0046",
    ("안지희", "4650"): "AJH4650", ("양대산", "5505"): "YDS5505", ("허윤영", "6754"): "HYY6754",
    ("한효주", "6913"): "HHJ6913", ("임호용", "6444"): "LHY6444", ("서완석", "7351"): "SWS7351",
    ("최재영", "1882"): "CJY1882", ("이찬미", "8153"): "LCM8153", ("지하은", "6954"): "JHE6954",
    ("유인호", "0881"): "YIH0881", ("진아영", "3243"): "JAY3243", ("김지연", "9275"): "KJY9275",
}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        bad = [(k, v, member_code(*k)) for k, v in ISSUED.items() if member_code(*k) != v]
        print("전체 일치" if not bad else bad)
        sys.exit(1 if bad else 0)
    print(member_code(sys.argv[1], sys.argv[2]))
