# medicube — Booster Pro X2 하이엔드 재해석 (2026-10-14 시작)

## 사용자 결정 (2026-10-14)
- 주인공: **Booster Pro X2 (디바이스)**
- 언어: **영어 우선**
- AI 생성 모델 컷 사용 OK (하단 AI 생성 표기)

## 방향
"메디큐브가 하이엔드 메종이라면" — 현재 사이트의 쿠폰 팝업·할인가·효능 % 수치·캡슐 버튼을 뺀다.
화이트/블러시, 큰 여백, 프레임당 제품 하나, 디돈 세리프 + 정밀 산세리프, 빛(LED 링)이 모션 주인공.
田中六五(세로 명조·실사 장면·어두운 호박색)·오니츠카(와시·먹·나무장)와 겹치지 않게.

## 원문 확인한 사실 (https://medicube.us/en-jp/products/booster-pro-x2, 2026-10-14 열람)
- 7 Modes: Booster / MC / Derma Shot / Air Shot / Dual / Mask / AI ("AI applies only to in-app custom mode recommendations")
- Dual-Head Tech · 6 Intensity Levels
- "Equipped with a skin contact sensor that emits LED light only when it touches the skin."
- What's included: Booster Pro X2 / User Manual / USB Charging Cable
- Colours: Pink / White
- How to layer (with skincare): Booster X2 > MC X2 > Derma Shot X2 > Dual
- 모드 색(공식 이미지 BoosterProX2_03·01): Booster 주황, MC 초록, Derma Shot 노랑-주황, Air Shot 하늘색, Mask 보라(01 화면 MASK + 보라 발광)
- 쓰지 않는 것: 효능 % (Clinical), "Global No.1"(Amazon 판매 기준 각주), 가격/할인, 피부과 의사 추천 문구 — 하이엔드 톤 + 일본 薬機法 고려

## 장면 구성 (초안)
0. Hero — 블러시 무대 위 기기가 천천히 회전 (Blender 시퀀스)
1. Anatomy — 머리 부품이 들려 올라가는 분해도: 엠블럼 면판 / LED 링 / 크롬 칼라 / 몸통 + 사양 라벨
2. Seven modes — 머리 클로즈업, 스크롤마다 모드 색으로 발광 + 빛의 동심원 링 (렌더 + 코드)
3. Ritual — AI 모델 컷 (Gemini), 공식 사용 순서 Booster → MC → Derma Shot → Dual
4. Display — 화면 UI (MASK / 단계 / 0:00) 클로즈업
5. Pink / White — 두 색 나란히
6. Close — 공식 제품 페이지 링크, 컨셉 작업·AI 생성 표기

## 기준 자료
`ref/` — medicube.us 공식 상품 이미지 4장 (사용자 허락 후 다운로드, 형태·색 기준으로만 사용)

## 진행 (2026-10-14 저녁, 사용량 한도로 중단)
- 완료: 기준 이미지 4장(`ref/`), 텍스처 생성 `tools/make_textures.py`(몸통 인쇄·MODE 버튼·세로 로고·화면 UI·엠블럼·칼라 슬롯), Blender 조립·렌더 `tools/render_device.py`(옵션: --color pink|white, --led 모드색, --explode, --cam hero|head|wide, --frames).
- 첫 테스트 렌더 `render/t_hero.png`: 형태·화면·칼라는 나옴. 문제 — ①전체가 과노출이라 핑크가 너무 옅고 배경이 블러시가 아니라 흰색으로 보임(조명 세기/노출 낮출 것) ②카메라가 수평이라 머리 윗면(엠블럼 렌즈)이 안 보임(실물 사진처럼 위에서 내려다보게 camz 올릴 것) ③기기가 화면에서 작음(거리 줄일 것).
- 다음: 위 3개 수정 → 실물 사진(ref/BoosterProX2_08.jpg)과 나란히 비교 → 머리 클로즈업 LED 7색 렌더 → 페이지 구성. Gemini 모델 컷 프롬프트는 아직 안 줌.

## 진행 (2026-10-14 밤, 재개)
- 렌더 수정 완료: 색 변환을 AgX → **Khronos PBR Neutral**(제품 색 재현용), 노출 −2.6 기본 + 화면·LED는 노출 보정(EXPK)으로 실제 밝기 유지.
  크롬이 하얗게 뜨던 원인 = 반사될 어두운 면이 없었음 → 검은 반사판(Flag L/R, Ceiling, 카메라에 안 보임) 추가.
- 머리 재구성(ref/_dev_head.png, ref/16_*.jpg 기준): 모드 색으로 빛나는 검은 링 → 매끈한 크롬 칼라(슬롯 제거, 윗면 막음) → 살짝 볼록한 반투명 캡 + **솟은 크롬 엠블럼(삼각 띠 + 가로 막대) 실제 지오메트리**.
- 몸통: 로고·MODE 잉크 진하게(160,112,118), MODE 버튼 범프, 화면 아래 전원 칸 분리선, 모드별 화면 텍스처(screen_<mode>.png).
- 어두운 배경(--bg dark): 기기용 로우키 조명으로 새로 잡음(Key 5, Rim 10, 약한 Glow 벽). LED 7색 확인.
- 시안 세트 렌더: `tools/render_draft.sh` → render/draft/ (hero_pink, hero_white, mode_7색)
- Gemini 프롬프트: prompts.md (기기는 넣지 않음 — 모양이 달라지므로)

## 광고 모션 방향 (2026-10-14, 사용자: "광고느낌의 모션그래픽을 넣으면 좋겠다")
공식 상품 페이지 영상(medicube.us, design-lab-resources.aprd.io/*.mp4 — 브라우저에서 보기만 함)에서 확인한 모션 문법:
①어두운 무대에 기기 여러 대가 줄지어 각자 모드 색으로 켜짐 ②낮은 앵글에서 머리 링 점화 ③머리를 감아 도는 빛 궤적(라이트 페인팅) ④모델 뺨에 빛 입자.
→ 같은 문법을 더 절제된 톤으로(느린 템포, 한 컷에 한 색, 가는 선).
컷 계획:
1. Ignition (tools/shot_ignite.py) — 낮은 앵글 → 링 점화 → 혜성 궤적 → 빛 고리 3번 → 엠블럼 공개. 4초. ← 시안 진행 중
2. Lineup — 7대가 줄지어 차례로 모드 색 점화, 카메라 측면 이동
3. Anatomy — 머리 부품 분해(--explode) + 빛 선
4. Ritual — Gemini Night 컷 + 화면에서 빛 번짐(코드)
5. Pink/White — 블러시 무대 턴테이블
웹: 히어로는 광고 필름 루프, Anatomy·Lineup은 스크롤 스크럽.

## 모드 공식 설명 (medicube.us/en-jp/products/booster-pro-x2, 2026-10-15 열람) — 모드별 분위기 연출의 근거
- BOOSTER X2: "Boost Active Absorption / Glow care from within" (2X GLOW BOOSTING)
- MC X2: "Skin Firming Care / For Smoother, Plump-Looking Skin" (2X BOUNCE BOOSTING) — 'microcurrent'라는 표현은 공식 문장에서 확인 못 함(리뷰에만 있음) → 쓰지 않음
- DERMA SHOT X2: "Facial Definition Care / Delivers Energy for Sculpted-Looking Skin" (2X SKIN-DEFINING)
- AIR SHOT X2: "Pore Refining Care" (2X PORE REFINING)
- DUAL X2: "Two Modes At Once / Combine two care modes at once"
- MASK X2: "for better synergy / *Use only with sheet masks"
- AI X2: "Smart App Connected Care / *AI applies only to in-app custom mode recommendations"
- 효능 % 수치는 계속 쓰지 않음.
분위기(사용자 지시 2026-10-15): 부스터=부스터 느낌, 더마샷=촘촘한 바늘/전기, 에어샷=구름 위로 떠오름, 마스크=촉촉함, AI=분석.
MC·DUAL은 사용자가 모름 → 공식 설명 기준으로 MC=탄력·튕김(bounce), DUAL=두 개가 겹쳤다 하나로.
- FAQ 원문 (같은 페이지 "What are the new Dual Mode, Mask Mode, and AI Mode features?", 2026-10-15 펼쳐서 확인):
  "Dual Mode lets you combine two modes at the same time ... Dual Mode combinations can be customized in the AGE-R App."
  "Sheet Mask Boost Mode is designed to be used over a sheet mask to help maximize the absorption of the remaining essence"
  "AI Mode analyzes your skin condition and skincare habits to recommend a personalized care routine. ... exclusively through the AGE-R App."

## 모드별 인터랙션 장면 (2026-10-15~)
- 공통: 흰 무대 + 분홍 콜라겐 젤리 푸딩(tools/shot_pudding.py --mode …), 문구는 공식 카피에서 "2X"만 뺀 것을 3D 젤리 글자(Nunito Black)로, 기기 양옆으로 갈라 배치. 렌더: `zsh tools/render_pudding.sh mc|derma <버전>`
- 립스틱 글씨(tools/lipstick.py)는 사용자가 젤리 글자로 교체 지시 → 보관만.
- MC: 거꾸로 떨어져 30% 꽂힘, 푸딩 출렁임. 문구 "Bounce Boosting". 승인(v7, 다듬기 후 v8).
- DERMA SHOT: MC 끝 상태에서 시작, 헤드에서 바늘 72개가 두 번 튀어나와 모드색(노랑-주황)으로 빛남 → 기기를 뽑음 → 젤리가 따라 늘어났다 놓이고 구멍이 메워짐. 실제 기기에 바늘은 없음 — 은유로만 씀. 문구: 젤리 "Skin Defining" → 전기 글자(tools/electric.py) → 사용자 "효과 크게 안 줘도 됨" → **"DERMA SHOT" 바늘 점 글씨(tools/pinprick.py)** 채택(v3). 바늘 쏠 때 점이 찍혀 글자가 생기고, 이후 정지.
- Fredoka·Rubik·Quicksand는 윤곽선이 겹쳐 Blender 글자 채움이 깨짐 → Nunito Black 사용.
- AIR SHOT (v1): 흰 무대에서 서 있던 기기가 앞으로 살짝 쏠렸다가 뒤로(옆으로 약간 돌며) 넘어감 → 배경이 하늘로 바뀌고 구름이 올라와 받아 줌 → 화면·로고가 보이게 누운 채 구름에 파묻혀 둥실. 문구 "AIR SHOT"(Quicksand Bold, 에어 파랑, 효과 없이 안개에서 나오듯). 구름은 metaball. 렌더: `zsh tools/render_air.sh <버전>` (tools/shot_air.py, tools/comp_air.py)
- AIR SHOT v3 (2026-10-16): 사용자 지시로 ① 똑바로 뒤로 넘어짐 + 카메라가 따라가 위에서 내려다봄(누운 기기가 화면에선 세워진 듯 보이는 게 맞음 — 가로 구도 아님) ② "AIR SHOT"은 구름 왼쪽 옆 ③ 착지 반동(쿵) 제거 ④ 구름은 거품 같다 → 볼륨 구름(metaball→Mesh to Volume→Volume Displace, Principled Volume 흡수색 흰색, 구름 전용 햇빛 light linking 30*EXPK). 프레임당 약 27초. 이전 metaball 표면판은 tools/shot_air_v2.py.
- AIR SHOT v4 (2026-10-16): 사용자 "구름 텍스처 부족 / 얹힌 느낌, 파고드는 느낌 없음" → 변위 2단(큰 굴곡+잔굴곡), 속 채움(nfloor 0.85, density 3000), 구름 전용 하늘빛 보조광, 조리개 f16, 착지 후 1.5초간 30mm 더 가라앉음 + 기기 양옆 구름(Wrap)이 부풀어 감쌈. 프레임당 약 48초. v3 코드는 tools/shot_air_v3.py.
- AIR SHOT v5 (2026-10-16): 사용자 "구름 질감 / 파묻히는 게 연속동작(멈췄다 내려가기 X) / 글씨도 구름느낌" → 변위 3단(잔물결 추가, voxel 0.0015), 햇빛 더 낮게, 넘어짐→착지→파고듦을 한 시계(F_TIP~F_LAND+22)로 묶음, "AIR SHOT"을 같은 볼륨 구름으로(Nunito Black→Mesh to Volume) — 구름과 한 번에 렌더하면 프레임당 ~4분이라 글씨는 카메라 고정 1장(--pass text)만 렌더해 comp에서 노이즈로 응결. 렌더 약 1.5시간. v4 코드는 tools/shot_air_v4.py.
- AIR SHOT v6 (2026-10-16): 사용자 "덜 잠기게, 푹신한 쿠션에 떨어지듯(지금은 로켓 착지), 오른쪽 팔 구멍 메움, 안착 때 구름 살짝, 텍스트 텍스처" → 중력 가속 낙하(sgl^2)→쿠션 침하 10mm+작은 되돌림, 구름 한 번 살짝 눌림(출렁임 없음), 바닥 코어 공으로 구멍 제거, 글씨 변위 강화. v5 코드는 tools/shot_air_v5.py. ("구름이 살짝" 뒷말은 미수신 — 눌림으로 해석)
- AIR SHOT v7 (2026-10-16): 사용자 "화면 흔들림 수정, 쿵이 아니라 푸욱" → 카메라는 기기 위치를 매 프레임 따라가지 않고 시작→최종 구도로 한 번에 부드럽게 이동, 착지 후 되튐 없이 20프레임 감속하며 18mm 가라앉음, 구름도 함께 서서히 눌림. v6 코드는 tools/shot_air_v6.py.
- AIR SHOT v8 (2026-10-16): 사용자 "늦게 올라온다 = 옆에서 차오르는 구름(Wrap) 없애라는 뜻", "푸딩처럼 얹힐 때 탱글하게 옆으로 밀렸다 돌아오기", "OT 뒤 구름 제거" → Wrap 숨김, JELLY(t) 감쇠 진동으로 구름 xy 퍼짐·z 눌림 + 기기가 표면 따라 탐, 구름 왼쪽(local y>0.055) 깎음. 구름 올라오는 타이밍은 v7 그대로. v7 코드는 tools/shot_air_v7.py.
- AIR SHOT v9 (2026-10-16): 사용자 "랜딩 때 투둑거림 / 구름 위아래 흔들림 없애기" → 원인은 회전이 최고속에서 착지 프레임에 딱 멈춘 것. 넘어짐을 F_TIP~F_LAND+6 한 시계로 가속 후 감속(sstep(s^1.4)), 착지 후 숨쉬기 bob·좌우 롤 제거, 푸딩 반응은 한 번 밀렸다 돌아오기만(진동 없음). v8 코드는 tools/shot_air_v8.py.
- AIR SHOT v10 (2026-10-16): 사용자 "착지 때 기기 밑 부자연스러움, 완전히 넘어갔을 때 한꺼번에 닿기" → 원인: 밑동 회전축이 구름 윗면보다 낮아 넘어지는 내내 밑동이 구름에 묻힘. 구름 윗면을 누운 기기 아랫면 높이(-R)에 맞추고 순수 피벗 회전, 수평이 되는 순간 몸통 전체 접촉 후 16mm 침하. 넘어짐 곡선 표 읽기 반올림 → 보간(프레임별 회전량 ±10% 떨림 원인). v9 코드는 tools/shot_air_v9.py.
- AIR SHOT은 v10으로 승인(2026-10-16 "ㅇㅇ").
- DUAL 시안 v1 (2026-10-16): 공식 "Two Modes At Once" → 화면을 비스듬히 둘로 나눠 기존 장면 두 개 동시 재생(MC|DERMA → DERMA|AIR → AIR|MC, 각 1.5초), "DUAL"은 나눈 선 기준으로 양쪽 모드 색. 실제로 어떤 모드끼리 조합되는지는 미확인(앱에서 설정) — 조합을 주장하지 않음. tools/comp_dual.py, MC 글자 없는 판 render/pud_mc_nt.
- DUAL은 모든 장면을 만든 뒤 마지막에 섞기로(사용자 2026-10-16).
- MASK 시안 v1 (2026-10-16): 공식 "Use only with sheet masks" — 물은 촉촉함 무드일 뿐 주장 없음. 흰 무대에 서 있던 기기(보라 LED) → 물이 아래부터 차올라 화면을 잠금 → 기기가 부력으로 떠서 천천히 흔들림, 물결 빛·기포, "MASK"는 물기 어린 투명 글씨. 기기만 3D(tools/shot_mask.py), 물은 comp(tools/comp_mask.py) 시안.
- MASK 시안 v2 (2026-10-16): 사용자 "퐁당 빠지는 걸로" → 반수면 구도(위 30% 공기, 아래 물), 기기가 위에서 떨어져 퐁당(물방울·물기둥·수면 고리·기포 꼬리), 물속에서 감속해 가라앉았다 떠오름, 이후 수면이 올라와 화면 전체가 잠기고 "MASK". 물은 아직 2D 합성 — 실제 물 시뮬레이션은 미착수. v1 코드는 tools/shot_mask_v1.py, tools/comp_mask_v1.py.
- MASK 시안 v3 (2026-10-16): 사용자 "물이 나중에 차오르지 말고 카메라가 기기 따라 내려가며 물이 차오르는 걸 보여주기" → 퐁당 후 기기가 화면 가운데에 오면 카메라가 따라 내려감(수면이 0.30H→화면 밖), 기기 더 깊이 가라앉음, 프레임별 수면 위치는 render/mask_path.json(water_y_f). v2 코드는 tools/shot_mask_v2.py, tools/comp_mask_v2.py.
- MASK v4 (2026-10-16): 흐름 승인("흐름은 맞아"), 물색을 연보라 → 맑은 파란빛으로(사용자). 보라는 기기 LED에만. 물 튀김은 아직 2D 합성 — 실제 물 시뮬레이션 여부 미정.

### MASK 물리 시뮬레이션 시험 (2026-10-16, Mantaflow FLIP)
- 1차 res200 실속도 1.2 m/s 수직 입수: 물보라 거의 없음(render/mw_sheet.png), 34프레임 굽는 데 16분
- 2차 유체 시간 0.35배(물리 입수속도 ~3.4 m/s): 공동이 닫히며 작은 물기둥만(render/mw2_sheet.png)
- 3차 옆으로 55° 기울여 입수(--tilt_in 55, res110): 물속 공기 꼬리는 생기나 수면 위 물보라는 여전히 없음(render/mw3_sheet.png)
- 결론: 수면 위 왕관형 물보라가 세 번 다 안 나옴. 물 자체도 탁한 판처럼 렌더됨. 2D 합성 v4 가 더 나음 → 사용자 판단 대기
- 옵션: shot_mask.py --water 1 --bake 1 --fres --fend --tscale(기본 0.35) --tilt_in(기본 0)
- 2026-10-16 사용자 「아니야 옆으로 하자」 → 옆 55° 입수로 확정. 해상도 2.2mm(res 282) 화면 전체 범위로 본 계산
  - 1회차(render/mask_sim_leak): 물보라는 좋으나 이후 물이 계속 줄어 f120 에 기기가 수면 위로 나옴(수위 z90 0.097→-0.248, 경계는 전부 닫혀 있음)
  - 저해상도 대조: fractions off/band 3 은 약간 줄고, fractions on/band 10 은 유지 → --band 10 으로 재계산 중, f61 에서 수위 확인
  - 합성: tools/comp_mask_sim.py (v4 파란 톤으로 색보정 + 잔물방울 + MASK 글씨), 수위 확인: tools/fluid_level.py
  - band 10 은 res 282 에서 입자 할당 오류로 1프레임에서 중단 → band 5(7부터 중단) + 2차 입자 끔으로 재계산, 수위 유지 확인(z90 0.096→0.125, 출렁임 포함)
  - 결과: render/mask_v5.mp4 (합성 render/mask_sim_c, 원본 render/mask_sim). 남은 결함: 왼쪽 세로 밝은 띠(수조 옆면 반사로 추정), 솟은 수면 일부가 색보정선 위라 하얗게 보임
- 2026-10-17 사용자: 기기에 붙는 버블 제거 / MASK 글씨는 공기로 / 조명 있는 밝은 느낌 → render/mask_v6.mp4
  - 재계산 없이 tools/render_mask_cache.sh (shot_mask.py --from_cache 1: 캐시 메시를 프레임마다 직접 불러옴. REPLAY 는 캐시를 덮어써서 금지, 캐시 좌표는 가장 긴 변 기준 균일 배율)
  - 버블: 물보라 가라앉은 뒤(F_HIT+8→+14) 기기 주변 7mm 물 표면을 투명 처리. 수조 앞·뒤·옆면도 투명(세로 띠·모서리 사각형 제거) → 물 색은 합성에서
  - 합성 tools/comp_mask_sim.py --ref 247,243,241: 밝은 파랑 + 비스듬한 빛줄기 + 위쪽 밝기, 그물 무늬 제거, 공기 방울로 채운 MASK(f66부터 떠올라 모임)
  - Blender 언어가 한국어로 바뀌어 노드 이름 오류 → 모든 렌더 스크립트에 --factory-startup
- 2026-10-17 사용자: 공기가 카툰 같다 / 너무 늦게 올라온다 → render/mask_v7.mp4
  - 공기 방울을 3D 로: tools/air_letters.py(배치 → render/mask_air.json) + tools/mask_air.py(shot_mask.py --air 1, 공기/물 IOR 유리, 투명 필름 유리, 서브프레임 핸들러로 움직임 번짐) → render/mask_air
  - f30(카메라가 물에 들어간 직후)부터 떠올라 f42 쯤 글자 완성 (v6 는 f66 시작, f90 완성). 화면 전체의 2D 잔방울도 3D 로 교체
  - 합성: comp_mask_sim.py --air render/mask_air
- MASK 는 v7 로 승인(2026-10-17 "좋아"). 다음: AI 장면
- AI 시안 v1 (2026-10-17): MASK 끝 구도에서 시작 → 수면이 내려가며 물 빠짐(2D, MASK v7 물색·빛줄기), MASK 공기 글씨 위로 사라짐, 떠 있던 기기가 물과 함께 내려와 흰 바닥에 섬(젖은 바닥 반사) → LED MASK 보라→AI 흰빛(두 패스 교차) → 빛줄기 스캔 + 윤곽선·측정점 → 점이 모여 점 행렬 "AI" + 공식 "Smart App Connected Care" + 각주. 수치·피부 데이터 없음. 실제 광고 레퍼런스는 못 찾고 판단으로 잡음.
  - tools/shot_ai.py, tools/comp_ai.py, zsh tools/render_ai.sh <ver> [comp] → render/ai_v1.mp4
- AI v2 (2026-10-18, 사용자 지시 2026-10-17): MASK 글씨 아래 바닥에 구멍 → 물리 시뮬레이션으로 물이 구멍으로 빠짐(Mantaflow 배출구, 소용돌이 힘은 물을 튀겨 제거), MASK 공기 글씨는 소용돌이치며 구멍으로 빨려 들어감, 기기는 그대로 떠 있음, 카메라는 MASK 끝 구도에서 올라가 바닥을 내려다봄 → 기기 링에서 레이저가 구멍을 훑고 테두리를 그림 → 뚜껑에서 전기가 구멍 테두리로 튀고 다이아몬드 그물을 짜서 막음 → 그물 위에 빛으로 "AI" 써짐 + 공식 문구·각주. 7.5초(180프레임)
  - tools/shot_ai.py(물·바닥·구멍·기기, --fx 1 이면 tools/ai_fx.py), tools/comp_ai.py, zsh tools/render_ai.sh <ver> [bake|main|fx|comp] → render/ai_v2.mp4. v1 은 tools/shot_ai_v1.py·comp_ai_v1.py
  - 남은 점: 배수가 ~100프레임이라 레이저(92) 시작 때 얇은 물이 남음 / MASK 끝과 AI 시작의 물색 차이
- AI v3 (2026-10-20, 사용자 "ai는 바꾸자"): 구멍·레이저·그물(v2)은 폐기. MASK 끝에서 물이 화면 밖 양끝 바닥으로 자연스럽게 빠짐(Mantaflow, 수면이 지나갈 때 MASK 공기 글씨가 터짐) → 배경이 흰 무대에서 검정으로(밝은 패스/스폿 패스 교차) → 기기가 왼쪽 아래→오른쪽 위 대각선으로 기울며 카메라가 화면·뚜껑으로 다가감, 기기는 오른쪽 → 왼쪽 위에서 빛줄기 + 떠다니는 먼지 → 왼쪽에 "AI"(Bodoni Moda) / SMART APP CONNECTED CARE / FAQ 원문 첫 문장 / 공식 각주. 7초(168프레임)
  - tools/shot_ai.py(--bg white|dark, --from_cache, --path 1), tools/comp_ai.py, zsh tools/render_ai.sh <ver> [bake|white|dark|comp] → render/ai_v3.mp4. v2 는 *_v2.py, render_ai_v2.sh
  - FAQ 뒷문장("...exclusively through the AGE-R App")은 앞부분 미확인이라 안 씀
- 레퍼런스 3개 검토 (2026-10-21, 사용자 「필요한거 넣고 불필요한건 이유」): @every._ai 「웹사이트 프롬프트 8가지」 → 웹페이지 단계 틀로 채택, web_checklist.md 로 정리(판매 페이지용 항목은 뺌). @luna_workwithai 「바이브 코딩 사이트 TOP3」(motionsites.ai · blog.vibecoder.me · Manus, #PR 협찬)와 @every._ai 「클로드 숏폼 공장」은 이 프로젝트에 안 넣음.
- AI v4 시안 (2026-10-21, 사용자: 물 빠짐 어색 / 그냥 어두운 배경 → 공간감 있는 어두운 스튜디오 / 조명 저렴·먼지 빼기 / 기기 천천히 회전 / 플라스틱 덩어리 → 고급 재질 / 폰트·설명 과다 / AI 글씨 별로)
  - 레퍼런스(10/21 Behance 직접 열람): PX-01(어두운 회색 스윕 + 제품 뒤 벽의 부드러운 빛 웅덩이 + 바닥), CCLIME(원통 몸통에 긴 하이라이트 한 줄). 텍스트는 제품명 + 작은 한 줄.
  - 원인: v3 는 기기만 투명 렌더 후 검정을 깔고 2D 원뿔 빛을 그렸음 → 공간·조명이 없음. 몸통은 거칠기 0.42 하나라 하이라이트가 퍼짐.
  - shot_ai.py --bg studio: 실제 스윕(바닥=수조 바닥 -0.20 → 뒷벽 y 0.95), 뒷벽 스폿 빛 웅덩이, 반사 전용 발광판(HiLine·HiSoft, 확산광·그림자 없음)으로 하이라이트 줄, 왼쪽 소프트박스 키, 뒤 림 2개, 피사계 심도 f/4(초점은 몸통 표면). --mat lacquer|pearl. 기기가 자기 축으로 360° 천천히 회전(가감속, 끝에 화면이 정면). 216프레임(9초).
  - 물: 양 끝 배수구 → 바닥 전체 배수(수면이 고르게 내려감), 캐시 render/ai_fluid4 (FEND 110).
  - 글씨: FAQ 문장 삭제 → "AI" + SMART APP CONNECTED CARE + 공식 각주. A안 빛의 선 / C안 Manrope ExtraLight. B안(3D 반투명 글자)은 둔해서 제외. tools/ai_type_draft.py
  - 시안 시트 render/ai4_draft_sheet.png. v3 코드는 *_v3.py / render_ai_v3.sh
- AI v4 완성 (2026-10-21, 사용자 「글씨는 a안」「글이 나와 있을 때도 천천히, 모니터가 보이는 선에서」) → render/ai_v4.mp4 (10초, 240프레임, 시트 render/ai_v4_sheet.png)
  - 물: 바닥 전체 배수는 0.5초 만에 빠져서(자유 낙하) → 배수 틈 4개를 바닥에 고르게(--slots 4). 수면이 고르게(좌우 차 1cm 이하) 기기를 약 27프레임 동안 지나 내려가고 바닥 가까이서 느려짐. 캐시 render/ai_fluid4 (FEND 70)
  - 수면 기준으로 위=스튜디오·아래=MASK 물빛으로 가르면 화면 분할(와이프)처럼 보여 폐기 → f4~30 동안 MASK 밝은 물빛 전체가 스튜디오로 서서히 넘어감(물 빠지며 조명이 내려가는 흐름). 스튜디오 패스에선 수면보다 1.5mm 위의 물(기기에 달라붙은 막·덩어리)은 투명, 대신 몸통에 물방울(보로노이 범프, 끝에 35% 남음)
  - 회전: 한 바퀴(최고 64°/s) 뒤 F_TXT(150) 부터 화면 정면 ±40° 범위를 20°/s 로 계속 회전
  - 글씨 A안: 빛의 선이 그어 쓰는 "AI"(20프레임) → SMART APP CONNECTED CARE → 공식 각주. 빔·먼지 없음
  - zsh tools/render_ai.sh v4 [bake|white|studio|comp]
- AI v5 (2026-10-21, 사용자 「다가오는 거 더 빠르게, 물 빠지고 텍스트까지 너무 길어, 반사도 거슬려」) → render/ai_v5.mp4 (7.3초, 174프레임, 시트 render/ai_v5_sheet.png)
  - 카메라 이동 F_TURN0 24 → F_TURN1 64(40프레임, v4 는 80), 글씨 F_TXT 90(물 빠진 뒤 약 2.6초), FR 174
  - 반사: 스윕 바닥 Specular 0·Roughness 0.95, 기기 밑으로 빠진 물은 f26~34 에 투명으로 페이드(WaterFade)
  - 맞바꿈: 글씨 전 한 바퀴가 짧아져 최고 약 130°/s. 빠르면 → 한 바퀴 없이 화면이 보이는 범위에서만 회전하는 안
- AI 는 v5 로 승인(2026-10-21 「좋아 부스터로 넘어가자」). 다음: BOOSTER

## BOOSTER (2026-10-21~)
- 사용자 지시(2026-10-15): "부스터는 피부 층을 보여주면서 (안좋은) 회복되는". 공식: "Boost Active Absorption / Glow care from within"(2X GLOW BOOSTING → "Glow Boosting"). 공식 페이지 BOOSTER X2 MODE 그림(10/21 열람): 기기 머리를 볼에 대면 주황 물결 선이 피부 속으로 퍼짐 + 촉촉한 광. 피부 단면을 쓰는 실제 광고 레퍼런스는 Behance 검색으로 못 찾음(단면 모양은 판단).
- 시안(tools/shot_booster.py): 흰 무대·MC 카메라 계열(렌즈 50). 피부 블록 한 덩어리, 높이로 3층(아래 크림 · 가운데 분홍 · 겉 살구), 겉/가운데 경계 물결. 처음: 채도 낮고 탁함, 잔 건조선, 에센스 방울. 기기 거꾸로 내려와 머리를 표면에 댐(F24) → 주황 고리 3개가 접점에서 퍼짐(표면+단면) → 방울이 고리 지날 때 스밈 → 따뜻해지고 겉면 매끈·광택(F34~72), 가운데 층 안쪽 발광 → F96 기기 위로 빠짐(MC 가 위에서 떨어지며 시작). 글씨 "Glow Boosting" 기기 양옆 + BOOSTER MODE(배치 시안은 2D, 본편은 3D 안에서 빛나는 글자 예정).
- 시안 시트 render/booster_draft_sheet.png
- 사용자(2026-10-21): "피부를 여러 가지 내용으로 표현하고 있는데 이건 너무 피부를 보여주는 느낌, 케이크 같은 걸 보여주는 건?" → 케이크로 전환. 둥근 레이어 케이크(시트/크림 교대 + 위 글레이즈), 카메라 쪽 한 조각(62°) 잘라 단면. 처음: 마르고 구멍 숭숭한 시트·탁하고 잔금 간 글레이즈 + 시럽 방울(제과에서 시트를 적시는 시럽 = Active Absorption 비유) → 기기가 글레이즈에 머리를 대면 주황 고리 → 시럽 스밈 → 시트 촉촉·크림 매끈·거울 글레이즈, 층 안쪽 발광. 피부 블록판은 tools/shot_booster_v0skin.py
- 사용자(2026-10-21): "케이크가 맛있어 보이지 않아, 실제 케이크를 확인해서 유사하게" → Unsplash 실사진 2장 확인(딸기 쇼트케이크 조각: 고운 노란 시트·두꺼운 흰 크림층·크림 속 딸기 단면·겉 생크림 / 한 조각 자른 딸기 무스 케이크: 분홍 윗면·테두리에 크림 로제트와 반 자른 딸기). v2: 겉 생크림(스패출러 결), 단면 시트/크림+딸기 단면/시트/크림+딸기/시트/얇은 크림, 분홍 글레이즈, 테두리 로제트 9 + 반쪽 딸기 9, 흰 접시. 시럽이 위층부터 아래로 스밈(Soak 깊이). v1 케이크는 tools/shot_booster_v1cake.py

### BOOSTER 케이크 v3 (10/21, 사용자 「그래픽이 저조해 제대로 된 딸기 생크림케이크로」)
- 레퍼런스: Unsplash 딸기 생크림케이크·프레지에 단면(10/21). 일본식 쇼트케이크 문법으로 재구성.
- 윗면: 큰 생크림 로제트 12개 + 각 로제트에 통딸기(꼭지 아래·끝 위). 밑단 셸 테두리 56개. 반쪽·꼭지(calyx)는 뺌 — 덩어리처럼 보였음.
- 단면: 스펀지 3층 / 크림 2층(16~17mm), 크림층마다 반쪽 딸기 4개, 단면이 자른 면에 정확히 붙고 각도·높이 조금씩 흐트러뜨림.
  딸기 단면 = 붉은 테두리 → 분홍 과육 → 흐린 흰 심(타원 스티커처럼 보이던 것 수정). 딸기 길이 = 폭의 1.3배.
- 스펀지: 노이즈로 휜 보로노이 기공 + 기공 범프 + 얼룩. 조각 각도 62°→90°(단면이 잘 보이게).
- 카메라 camd 0.80 / camz 0.31 / lookz 0.125 — 기기 윗부분 잘리던 것 수정.
- 시안: render/booster_draft_sheet.png (f12 전 / f40 링 / f84 후). 이전 단계 스크립트: shot_booster_v3a.py.
- 2026-10-22 사용자 「ㅇㅇ 다듬고 글자 넣어서 진행해줘」 → 케이크 v3 확정. 다듬기: 단면 생크림에 미색 얼룩·칼자국 결, 처음 상태 딸기를 마지판처럼 보이지 않게(채도 0.72·명도 0.84, 거칠기 0.40).
- 글자 "Glow Boosting": MC "Bounce Boosting" 과 같은 Nunito Black 3D 글자(두 "Boosting" 줄이 운을 맞춤), 케이크 뒤 기기 양옆. 우윳빛 복숭아색 재질 + 안쪽에서 주황 발광(두꺼운 가운데일수록 밝게) + comp 에서 따뜻한 번짐. F60 부터 기기 쪽에서 바깥으로 자라나고 F68~90 에 불이 들어옴. 작은 "BOOSTER MODE" 는 MC MODE 와 같은 서체·위치·자간, 주황 갈색.
  - Fraunces(세리프)는 w·B 윤곽이 겹쳐 그려져 Blender 채움이 구멍 남 → 폐기. 투명 유리 글자는 불 들어오기 전 거무스름 → 폐기.
- 타이밍: FR 132(5.5초). 기기 F24 착지 → 고리 F26~ → 회복 F34~72 → 글자 F60~ → 기기 F96 들어 올림. 렌더 zsh tools/render_booster.sh v1 → render/booster_v1.mp4
- BOOSTER v1 완성 (2026-10-22) → render/booster_v1.mp4 (5.5초, 132프레임, 960x540), 시트 render/booster_v1_sheet.png. 사용자 확인 대기
