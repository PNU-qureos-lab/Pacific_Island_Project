(function () {
  'use strict';

  const ko = {
    'Overview': '전체 현황',
    'Pacific Island Project · verified local archive': '태평양 도서국 프로젝트 · 확인된 로컬 보관 자료',
    'Sentinel‑2 Local Data Inventory': 'Sentinel‑2 로컬 자료 인벤토리',
    'Archive overview and workflow status': '보관 자료 전체 현황 및 워크플로 상태',
    'Tidung checklist status': '티둥 체크리스트 상태',
    'First processing scenes': '첫 처리 영상',
    'Location': '지역',
    'Selectable scene map': '선택 가능한 영상 지도',
    'Best low-cloud scene map': '저운량 우수 영상 지도',
    'Display': '표시 방식',
    'Natural-color RGB': '자연색 RGB',
    'Cloud removed (SCL mask)': '구름 제거 표시 (SCL 마스크)',
    'Cloud mask only': '구름 마스크만 표시',
    'Scene preview slider': '영상 미리보기 슬라이더',
    'Complete survey-window screening list': '전체 조사 기간 영상 스크리닝 목록',
    'Previous scene': '이전 영상',
    'Next scene': '다음 영상',
    'All layers ON': '전체 레이어 켜기',
    'All layers OFF': '전체 레이어 끄기',
    'Layer opacity': '레이어 투명도',
    'Coverage': '연구지역',
    'Survey windows': '조사 기간',
    'Recommended download': '권장 다운로드',
    'All candidates': '전체 후보',
    'Tidung readiness': '티둥 활용 준비도',
    'Method': '방법',
    'Study coverage': '연구지역 범위',
    'Five AOIs': '5개 관심지역',
    'Search only:': '검색 단계:',
    'Survey and comparison windows': '조사 및 비교 기간',
    'Recommended download manifest': '권장 다운로드 목록',
    'Download manifest CSV': '목록 CSV 다운로드',
    'Complete candidate catalogue': '전체 후보 영상 목록',
    'Scene examples': '영상 예시',
    'Tidung example scenes': '티둥 영상 예시',
    'All sites': '전체 지역',
    'Both levels': '전체 처리 수준',
    'All cloud values': '전체 구름 비율',
    '≤ 20% cloud': '구름 20% 이하',
    '> 20% cloud': '구름 20% 초과',
    'Tidung current archive and selection readiness': '티둥 보유 자료 및 선정 준비도',
    'How many scenes can we use now?': '현재 사용할 수 있는 영상은 몇 개인가?',
    'Available locally:': '로컬 보유 자료:',
    'Inventory role:': '인벤토리 역할:',
    'Required scene fields before use:': '사용 전 필수 영상 항목:',
    'Intended later use:': '향후 활용 목적:',
    'Planned inventory outputs:': '계획 인벤토리 산출물:',
    'Collection method': '자료 수집 방법',
    'Important:': '중요:',
    'Source:': '출처:',
    'SITE / AOI': '지역 / 관심지역',
    'ANCHOR': '기준일',
    'LEVEL': '처리 수준',
    'ACQUIRED': '촬영일',
    'GAP': '날짜 차이',
    'CLOUD': '구름',
    'TILE': '타일',
    'SIZE': '용량',
    'PRODUCT': '제품',
    'AREA': '지역',
    'SURVEY ANCHOR': '조사 기준일',
    'SELECTED DATE': '선정일',
    'STATUS': '상태',
    'Downloaded': '다운로드 완료',
    'Waiting': '대기 중',
    'PACIFIC ISLAND BENTHIC PROJECT · SATELLITE DATA COLLECTION': '태평양 도서국 천해저 프로젝트 · 위성자료 수집',
    'PlanetScope Dove Data Collection': 'PlanetScope Dove 자료 수집',
    'Sensor introduction, delivered-data summary and preprocessing plan': '센서 소개, 수령 자료 요약 및 전처리 계획',
    'Print / PDF': '인쇄 / PDF',
    '1. SuperDove introduction': '1. SuperDove 소개',
    '2. Delivered-data summary': '2. 수령 자료 요약',
    '3. Tidung readiness': '3. 티둥 활용 준비도',
    '4. Preprocessing plan': '4. 전처리 계획',
    '1. PlanetScope SuperDove introduction': '1. PlanetScope SuperDove 소개',
    'PlanetScope PSScene · SuperDove (PSB.SD)': 'PlanetScope PSScene · SuperDove (PSB.SD)',
    'DELIVERED PRODUCT': '수령 제품',
    'FILES PER SCENE': '영상별 파일',
    'SPATIAL DETAIL': '공간 해상도',
    'PROCESSING LEVEL': '처리 수준',
    'REFLECTANCE VALUES': '반사도 값',
    'COLLECTION CAPABILITY': '촬영 주기',
    'Eight SuperDove spectral bands': 'SuperDove 8개 분광 밴드',
    'study areas requested': '요청 연구지역',
    'study areas delivered': '자료 수령 지역',
    'PlanetScope scenes received': '수령한 PlanetScope 영상',
    'SR image + UDM2 + metadata per scene': '영상별 SR + UDM2 + 메타데이터',
    '2. Delivered-data summary': '2. 수령 자료 요약',
    'REQUESTED LOCATION': '요청 지역',
    'PROJECT PURPOSE': '프로젝트 목적',
    'REQUESTED DATE WINDOW': '요청 기간',
    'ACTUAL DATES DELIVERED': '실제 수령일',
    'SCENES RECEIVED': '수령 영상 수',
    'DELIVERY STATUS': '수령 상태',
    'Field validation': '현장자료 검증',
    'Before and peak bleaching comparison': '백화 전·최고 시기 비교',
    'Alternative site': '대체 지역',
    'Delivered': '수령 완료',
    'Not received': '미수령',
    '2.1 Location details and imagery': '2.1 지역별 영상 및 상세정보',
    'All layers ON': '전체 레이어 켜기',
    'All layers OFF': '전체 레이어 끄기',
    'Layer opacity': '레이어 투명도',
    'SCENES RECEIVED': '수령 영상 수',
    'How to read the imagery table': '영상 표 읽는 방법',
    'Clear (%)': '맑음 비율 (%)',
    'Cloud (%)': '구름 비율 (%)',
    'Haze (%)': '연무 비율 (%)',
    'Shadow (%)': '그림자 비율 (%)',
    'GSD at capture (m)': '촬영 GSD (m)',
    'Output pixel (m)': '출력 픽셀 (m)',
    'Planet quality': 'Planet 품질',
    'Satellite ID': '위성 ID',
    'Values supplied with the Planet imagery': 'Planet 영상과 함께 제공된 값',
    'LAYER ON MAP': '지도 표시',
    'IMAGE PREVIEW': '영상 미리보기',
    'SCENE ID': '영상 ID',
    'ACQUISITION (UTC)': '촬영시각 (UTC)',
    'CLEAR (%)': '맑음 (%)',
    'HAZE (%)': '연무 (%)',
    'SHADOW (%)': '그림자 (%)',
    'GSD AT CAPTURE (M)': '촬영 GSD (M)',
    'OUTPUT PIXEL (M)': '출력 픽셀 (M)',
    'PLANET QUALITY': 'PLANET 품질',
    'SATELLITE ID': '위성 ID',
    '3. Tidung-only retrieval readiness': '3. 티둥 산출 활용 준비도',
    'Verified Tidung inventory:': '확인된 티둥 자료:',
    'Required before selection:': '선정 전 필수 확인:',
    'Glint limitation:': '선글린트 자료 한계:',
    'Retrieval readiness:': '산출 준비도:',
    'Preliminary intended use of Tidung scenes:': '티둥 영상의 예비 활용 목적:',
    'Bleaching-comparison intention:': '백화 비교 활용 목적:',
    'Later products:': '향후 산출물:',
    '4. Preprocessing plan: from delivered SR to water reflectance': '4. 전처리 계획: 수령 SR에서 수체 반사도로',
    'COMPLETE INPUT SUPPLIED BY THE LAB': '연구실 제공 입력자료 완료',
    'TARGET AFTER AN APPROVED METHOD IS SELECTED': '승인된 방법 선정 후 목표',
    'Planet Surface Reflectance (SR)': 'Planet 지표 반사도 (SR)',
    'Validated aquatic reflectance / Rrs': '검증된 수체 반사도 / Rrs',
    'Current status:': '현재 상태:',
    'Organize and verify files': '파일 정리 및 검증',
    'Select usable scenes and pixels': '사용 가능한 영상과 픽셀 선정',
    'Prepare each study area': '연구지역별 자료 준비',
    'Prepare and co-register each study area': '연구지역별 자료 준비 및 공동정합',
    'Select and test a sunglint method': '선글린트 방법 선정 및 시험',
    'Produce and validate Rrs': 'Rrs 생성 및 검증',
    'COMPLETE': '완료',
    'PENDING REVIEW': '검토 대기',
    'PENDING': '대기',
    'METHOD NOT SELECTED': '방법 미선정',
    'PURPOSE': '목적',
    'REQUESTED': '요청 기간',
    'ACTUALLY RECEIVED': '실제 수령일'
  };

  const originals = new WeakMap();
  const excluded = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEXTAREA', 'CODE']);
  let current = localStorage.getItem('inventoryLanguage') === 'ko' ? 'ko' : 'en';
  let observer;

  function translateDynamic(value) {
    if (ko[value]) return ko[value];
    if (/^\d+ rows$/.test(value)) return value.replace(' rows', '개 행');
    if (/^\d+ candidates$/.test(value)) return value.replace(' candidates', '개 후보');
    if (/^\d+ scenes received$/i.test(value)) return value.replace(/scenes received/i, '개 영상 수령');
    return value;
  }

  function walkTextNodes() {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    return nodes;
  }

  function renderLanguage() {
    if (observer) observer.disconnect();
    for (const node of walkTextNodes()) {
      if (!node.parentElement || excluded.has(node.parentElement.tagName)) continue;
      if (!originals.has(node)) originals.set(node, node.nodeValue);
      const original = originals.get(node);
      if (current === 'en') {
        node.nodeValue = original;
        continue;
      }
      const trimmed = original.trim();
      if (!trimmed) continue;
      const translated = translateDynamic(trimmed);
      node.nodeValue = original.replace(trimmed, translated);
    }
    document.documentElement.lang = current;
    document.title = current === 'ko'
      ? document.title.replace('Data Collection & Download', '자료 수집 및 다운로드').replace('Data Collection — Standalone', '자료 수집 — 독립형')
      : document.title.replace('자료 수집 및 다운로드', 'Data Collection & Download').replace('자료 수집 — 독립형', 'Data Collection — Standalone');
    const englishButton = document.getElementById('inventoryLanguageEnglish');
    const koreanButton = document.getElementById('inventoryLanguageKorean');
    if (englishButton && koreanButton) {
      englishButton.setAttribute('aria-pressed', String(current === 'en'));
      koreanButton.setAttribute('aria-pressed', String(current === 'ko'));
      englishButton.style.background = current === 'en' ? '#fff' : 'transparent';
      englishButton.style.color = current === 'en' ? '#123c48' : '#fff';
      koreanButton.style.background = current === 'ko' ? '#fff' : 'transparent';
      koreanButton.style.color = current === 'ko' ? '#123c48' : '#fff';
    }
    if (observer) observer.observe(document.body, { childList: true, subtree: true });
  }

  const switcher = document.createElement('div');
  switcher.id = 'inventoryLanguageSwitcher';
  switcher.setAttribute('role', 'group');
  switcher.setAttribute('aria-label', 'Language / 언어');
  switcher.style.cssText = 'position:fixed;right:18px;top:18px;z-index:2500;display:flex;align-items:center;gap:2px;border:1px solid rgba(255,255,255,.72);border-radius:999px;background:#123c48;padding:3px;box-shadow:0 4px 16px rgba(0,0,0,.2)';
  function makeLanguageButton(id, label, language) {
    const button = document.createElement('button');
    button.id = id;
    button.type = 'button';
    button.textContent = label;
    button.style.cssText = 'border:0;border-radius:999px;background:transparent;color:#fff;padding:7px 10px;font:800 12px/1 system-ui;letter-spacing:.06em;cursor:pointer';
    button.addEventListener('click', function () {
      current = language;
      localStorage.setItem('inventoryLanguage', current);
      renderLanguage();
    });
    return button;
  }
  switcher.appendChild(makeLanguageButton('inventoryLanguageEnglish', 'ENG', 'en'));
  const separator = document.createElement('span');
  separator.textContent = '|';
  separator.setAttribute('aria-hidden', 'true');
  separator.style.cssText = 'color:rgba(255,255,255,.7);font:700 11px/1 system-ui';
  switcher.appendChild(separator);
  switcher.appendChild(makeLanguageButton('inventoryLanguageKorean', 'KOR', 'ko'));
  document.body.appendChild(switcher);

  observer = new MutationObserver(function () {
    if (current === 'ko') renderLanguage();
  });
  renderLanguage();
})();
