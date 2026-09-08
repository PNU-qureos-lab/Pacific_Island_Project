(function () {
  'use strict';

  const ko = {
    'Overview': '전체 현황',
    'Pacific Island Project · verified local archive': '태평양 도서국 프로젝트 · 확인된 로컬 보관 자료',
    'Sentinel‑2 Local Data Inventory': 'Sentinel‑2 로컬 자료 인벤토리',
    'Archive overview and workflow status': '보관 자료 전체 현황 및 워크플로 상태',
    'Tidung checklist status': '티둥 체크리스트 상태',
    'Tidung inventory status': '티둥 인벤토리 상태',
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
    'Complete available-data inventory': '전체 보유 자료 인벤토리',
    'Quick archive summary': '보유 자료 요약',
    'Open detailed SAFE-product table': '상세 SAFE 제품 표 열기',
    'Clearest metadata candidates': '메타데이터 기준 최저 운량 후보',
    'Inventory scope': '인벤토리 범위',
    'Every available Tidung product listed': '보유한 모든 티둥 제품 목록화',
    'available local SAFE products': '보유 로컬 SAFE 제품',
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
    'REVIEW REQUIRED': '검토 필요',
    'NOT AVAILABLE LOCALLY': '로컬 자료 없음',
    'METHOD NOT SELECTED': '방법 미선정',
    'PURPOSE': '목적',
    'REQUESTED': '요청 기간',
    'ACTUALLY RECEIVED': '실제 수령일',
    'Pacific Island Benthic Project · Satellite Data Collection': '태평양 도서국 저서생태 프로젝트 · 위성자료 수집',
    'PlanetScope Dove Data Inventory': 'PlanetScope Dove 자료 인벤토리',
    'Exactly what was delivered for the project, and how each site will be used.': '프로젝트에 실제로 수령된 자료와 지역별 활용 계획을 정리했습니다.',
    '1. Files delivered': '1. 수령 자료',
    '2. Delivery by site': '2. 지역별 수령 현황',
    '3. How we will use the data': '3. 자료 활용 계획',
    '4. Scene inventory': '4. 영상 인벤토리',
    'One complete PlanetScope SuperDove package was checked for every listed scene.': '목록의 모든 영상에 대해 완전한 PlanetScope SuperDove 패키지를 확인했습니다.',
    'For this project, Planet supplied 3 m, orthorectified 8-band surface-reflectance image clips and their matching quality masks. These are the source files for later image-quality review and, only after that, benthic and depth work.': 'Planet은 본 프로젝트에 3 m 정사보정 8밴드 지표반사도 영상과 대응 품질 마스크를 제공했습니다. 영상 품질 검토를 먼저 통과한 뒤 저서생태 및 수심 분석에 사용합니다.',
    'Delivered product': '수령 제품',
    'Files per scene': '영상별 파일',
    'Spatial detail': '공간 해상도',
    'Processing level': '처리 수준',
    'Reflectance values': '반사도 값',
    'Collection capability': '촬영 주기',
    '8-band Analytic Surface Reflectance': '8밴드 분석용 지표반사도',
    'SR GeoTIFF + UDM2 + XML/JSON metadata': 'SR GeoTIFF + UDM2 + XML/JSON 메타데이터',
    '3 m output pixels; 3.2–4.0 m GSD in this delivery': '출력 픽셀 3 m; 이번 수령 자료의 GSD 3.2–4.0 m',
    'Orthorectified and atmospherically corrected SR': '정사보정 및 대기보정된 지표반사도',
    'Unitless; stored as DN ÷ 10,000': '무차원 값; DN ÷ 10,000으로 저장',
    'Near-daily constellation coverage': '위성군 기반 거의 매일 촬영 가능',
    'Delivered package verified:': '수령 패키지 확인 완료:',
    '48 SR images, 48 UDM2 masks and 48 XML metadata files, with JSON/catalog records, across four ZIP archives.': '4개 ZIP에 SR 영상 48개, UDM2 마스크 48개, XML 메타데이터 48개와 JSON/카탈로그 기록이 있습니다.',
    'Verified delivery source:': '확인된 자료 위치:',
    'Product source:': '제품 정보 출처:',
    'Complete': '완료',
    'Why each site is in this inventory, the requested dates, and the files received.': '지역별 포함 목적, 요청 기간, 실제 수령 자료를 보여줍니다.',
    'Delivery result:': '수령 결과:',
    'Field validation': '현장자료 검증',
    'Bleaching comparison': '백화 비교',
    'Alternative site': '대체 지역',
    'Map': '지도',
    'Satellite': '위성영상',
    'Use the same delivered SR image, UDM2 mask and metadata together. No scene is final until it passes the later quality check.': '수령한 SR 영상, UDM2 마스크, 메타데이터를 함께 사용합니다. 이후 품질 검사를 통과하기 전에는 어떤 영상도 최종 선정하지 않습니다.',
    'Site': '지역',
    'Scenes': '영상 수',
    'Planned use': '활용 계획',
    'Before it is used': '사용 전 확인',
    'Main site:': '주요 지역:',
    'Bleaching comparison:': '백화 비교:',
    'Alternative bleaching site:': '대체 백화 비교 지역:',
    'run the full depth and fractional-coverage workflow and compare results with field/UAV reference data.': '전체 수심·피복률 분석을 수행하고 현장/UAV 기준자료와 비교합니다.',
    'Choose the clearest scene closest to the field date; check water quality and align it to the reference image.': '현장조사 날짜와 가장 가까운 맑은 영상을 선택하고 수질 상태를 확인한 뒤 기준영상에 정합합니다.',
    'compare selected baseline and bleaching-period dates.': '선정된 기준시기와 백화시기 영상을 비교합니다.',
    'use the clearest dates around the intended event windows.': '의도한 이벤트 기간 주변에서 가장 맑은 날짜를 사용합니다.',
    'compare the closest usable before/event dates.': '사용 가능한 백화 전·이벤트 날짜 중 가장 가까운 날짜를 비교합니다.',
    'Check the Allen Coral Atlas period, local water quality, coverage and alignment.': 'Allen Coral Atlas 기간, 지역 수질, 영상 범위와 정합을 확인합니다.',
    'Use closer but lower-quality dates only as sensitivity checks.': '기간에 더 가깝지만 품질이 낮은 날짜는 민감도 검사에만 사용합니다.',
    'All selected scenes have Planet “test” quality, so local review is required.': '선정 영상은 모두 Planet “test” 품질이므로 관심지역 검토가 필요합니다.',
    'No PlanetScope analysis from this delivery.': '이번 수령 자료로는 PlanetScope 분석을 수행할 수 없습니다.',
    'PlanetScope data would need to be obtained first.': '먼저 PlanetScope 자료를 확보해야 합니다.',
    'Bleaching comparison: intended period → PlanetScope date to use': '백화 비교: 의도한 기간 → 사용할 PlanetScope 날짜',
    'Dates are candidates until the local reef AOI and Allen Coral Atlas event period are recorded.': '지역 산호초 관심영역과 Allen Coral Atlas 이벤트 기간을 기록하기 전까지는 후보 날짜입니다.',
    'Comparison': '비교 대상',
    'Initial intention from Allen Coral Atlas check': 'Allen Coral Atlas 확인에 따른 초기 계획',
    'Delivered PlanetScope dates to use': '사용할 수령 PlanetScope 날짜',
    'Decision': '선정 판단',
    'Before:': '백화 전:',
    'Peak:': '최고 시기:',
    'Baseline:': '기준시기:',
    'Bleaching period:': '백화시기:',
    'Backups:': '예비 날짜:',
    'Baseline candidate:': '기준시기 후보:',
    'Bleaching-period candidate:': '백화시기 후보:',
    'Sensitivity:': '민감도 검사:',
    'Timing checks:': '시기 민감도 검사:',
    'Primary comparison.': '주요 비교.',
    'Conditional comparison.': '조건부 비교.',
    'Quality-first comparison.': '품질 우선 비교.',
    'Alternative comparison.': '대체 비교.',
    'Cannot run.': '수행 불가.',
    'Both dates match the intended windows and have 96–100% whole-scene clear metadata.': '두 날짜 모두 의도한 기간과 일치하며 전체 영상 기준 맑음 메타데이터가 96–100%입니다.',
    'The 20 Jan scenes are cloudy/hazy; 29 Jan is clearer but three days outside the requested window. Select the clearest local 11 May strip.': '1월 20일 영상은 구름과 연무가 많습니다. 1월 29일은 더 맑지만 요청 기간에서 3일 벗어납니다. 5월 11일 영상 중 관심지역이 가장 맑은 스트립을 선택합니다.',
    'The closer 16 Dec scenes are hazy and 12 Jun includes cloud; use them only to test date sensitivity.': '기간에 더 가까운 12월 16일 영상은 연무가 많고 6월 12일 영상에는 구름이 있어 날짜 민감도 검사에만 사용합니다.',
    'These are the closest clear dates, but their Planet quality is “test”; inspect the reef AOI before acceptance.': '가장 가까우면서 맑은 날짜이지만 Planet 품질이 “test”이므로 선정 전에 산호초 관심영역을 확인합니다.',
    'No Fiji scenes were delivered.': '피지 영상은 수령되지 않았습니다.',
    'No PlanetScope dates available': '사용 가능한 PlanetScope 날짜 없음',
    'How Allen Coral Atlas and PlanetScope will be used together': 'Allen Coral Atlas와 PlanetScope의 연계 활용 방법',
    'Allen Coral Atlas identifies the event context; PlanetScope supplies the 3 m images used for this project comparison.': 'Allen Coral Atlas는 백화 이벤트의 시간·공간적 배경을 제공하고, PlanetScope는 본 프로젝트 비교에 사용할 3 m 영상을 제공합니다.',
    '1 · Record Atlas evidence': '1 · Atlas 근거 기록',
    '2 · Assign scene roles': '2 · 영상 역할 지정',
    '3 · Process both dates equally': '3 · 두 날짜 동일 처리',
    '4 · Compare results': '4 · 결과 비교',
    'Save the AOI, monitoring layer, bi-weekly period, bleaching class/thermal alert and access date.': '관심영역, 모니터링 레이어, 2주 기간, 백화 등급/열 스트레스 경보와 접근 날짜를 저장합니다.',
    'Label each Planet date as baseline, bleaching-period, backup or reject only after checking the recorded Atlas period.': '기록된 Atlas 기간을 확인한 뒤 각 Planet 날짜를 기준시기, 백화시기, 예비 또는 제외로 지정합니다.',
    'Apply the same water mask, haze/cloud/shadow and glint checks, co-registration, depth limits and common valid-pixel area.': '두 날짜에 같은 수체 마스크, 연무/구름/그림자 및 선글린트 검사, 공동정합, 수심 제한과 공통 유효 픽셀 영역을 적용합니다.',
    'Measure change in bottom/water reflectance and benthic or fractional coverage, then compare the spatial pattern with the Atlas bleaching layer.': '해저/수체 반사도와 저서생태 또는 피복률 변화를 계산하고 공간 패턴을 Atlas 백화 레이어와 비교합니다.',
    'Important interpretation:': '중요한 해석:',
    '“Baseline” means a candidate date outside the recorded bleaching event; it does not prove zero bleaching. “Bleaching-period” means the date overlaps or is nearest to the Atlas event window; one PlanetScope image alone does not prove that coral bleaching caused every brightness change. Allen Coral Atlas uses a pre-stress baseline and bi-weekly Sentinel-2 monitoring, so its dates are not a one-to-one match with single-day PlanetScope scenes.': '“기준시기”는 기록된 백화 이벤트 밖의 후보 날짜이며 백화가 전혀 없었음을 증명하지 않습니다. “백화시기”는 Atlas 이벤트 기간과 겹치거나 가장 가까운 날짜입니다. PlanetScope 한 장만으로 모든 밝기 변화의 원인이 산호 백화라고 증명할 수 없습니다. Allen Coral Atlas는 스트레스 이전 기준영상과 2주 단위 Sentinel-2 모니터링을 사용하므로 단일 날짜 PlanetScope 영상과 일대일로 대응하지 않습니다.',
    'Allen Coral Atlas monitoring method': 'Allen Coral Atlas 모니터링 방법',
    'Simple order of work:': '간단한 작업 순서:',
    'confirm the Atlas period → select and quality-check the PlanetScope pair → co-register common reef pixels → run depth/fractional-coverage comparison → report agreement and disagreement with the Atlas pattern. Tidung remains the field/UAV validation site.': 'Atlas 기간 확인 → PlanetScope 영상쌍 선정 및 품질 검사 → 공통 산호초 픽셀 공동정합 → 수심·피복률 비교 → Atlas 패턴과의 일치·불일치 보고 순서로 진행합니다. Tidung은 현장/UAV 검증 지역으로 유지합니다.',
    'Choose one site tab. Each row is one delivered scene; turn its layer on to see its footprint and preview.': '지역 탭을 선택하세요. 각 행은 수령 영상 한 장이며, 레이어를 켜면 촬영 범위와 미리보기를 확인할 수 있습니다.',
    'Position check:': '위치 확인:',
    'compare one layer at a time. When two transparent previews are ON, their overlap looks darker even without a large displacement.': '한 번에 한 레이어씩 비교하세요. 투명한 미리보기 두 개를 동시에 켜면 큰 위치 오차가 없어도 중첩부가 더 어둡게 보입니다.',
    'Overlap displacement:': '중첩 위치 오차:',
    'Turn on two or more overlapping scenes to see the measured displacement summary.': '중첩 영상 두 장 이상을 켜면 측정된 위치 오차 요약이 표시됩니다.',
    'Real image displacement': '실제 영상 위치 오차',
    'Yes. Scene geolocation can differ slightly. The Tongatapu 7 Jun 2024 pair differs by about 1.52 pixels (4.6 m), measured from stable land texture.': '영상 간 지리위치는 조금 다를 수 있습니다. 안정적인 육상 질감을 기준으로 측정한 Tongatapu 2024년 6월 7일 영상쌍의 차이는 약 1.52픽셀(4.6 m)입니다.',
    'HTML map display effect': 'HTML 지도 표시 효과',
    'The large dark diagonal is mainly created where transparent preview layers are stacked. It makes the difference look larger, but it is not the measured positional shift.': '큰 대각선 형태의 어두운 영역은 주로 투명 미리보기 레이어가 겹치면서 생깁니다. 차이가 더 크게 보이지만 측정된 위치 이동량은 아닙니다.',
    'How to read the imagery table': '영상 표 읽는 방법',
    'Percentages describe the entire satellite scene, not only the reef study area.': '백분율은 산호초 연구지역만이 아니라 전체 위성 영상을 나타냅니다.',
    'Area without cloud, haze, cloud shadow or snow. A high value means more potentially usable pixels.': '구름, 연무, 구름 그림자 또는 눈이 없는 영역입니다. 값이 높을수록 사용 가능한 픽셀이 많을 가능성이 큽니다.',
    'Area covered by opaque cloud where the surface cannot be seen.': '지표면이 보이지 않는 불투명 구름 영역입니다.',
    'Area with thin atmospheric interference. The surface may be visible, but its spectral value can be unreliable.': '얇은 대기 간섭이 있는 영역입니다. 지표가 보여도 분광값은 신뢰하기 어려울 수 있습니다.',
    'Area darkened by cloud or haze shadow. These pixels should normally be excluded from water analysis.': '구름 또는 연무 그림자로 어두워진 영역입니다. 일반적으로 수체 분석에서 제외해야 합니다.',
    'Approximate ground spacing of the sensor samples when the image was acquired. It changes slightly with altitude and viewing geometry.': '촬영 당시 센서 표본의 대략적인 지상 간격입니다. 고도와 관측 기하에 따라 조금 달라집니다.',
    'Size of each pixel in the delivered orthorectified GeoTIFF grid. Here it is fixed at 3 m, even when acquisition GSD differs.': '수령한 정사보정 GeoTIFF 격자의 픽셀 크기입니다. 촬영 GSD가 달라도 여기서는 3 m로 고정됩니다.',
    'Identifier of the individual SuperDove spacecraft that captured the scene.': '영상을 촬영한 개별 SuperDove 위성의 식별자입니다.',
    'Provider metadata plus a preliminary overlap-alignment check against one reference scene per site.': '제공자 메타데이터와 지역별 기준영상에 대한 예비 중첩 정합 검사 결과입니다.',
    'Overlap alignment': '중첩 정합',
    'Reference': '기준영상',
    'Manual check': '수동 확인',
    'Purpose': '목적',
    'Requested': '요청 기간',
    'Actually received': '실제 수령일',
    'Field-survey validation': '현장조사 검증',
    'Before / peak bleaching comparison in 2024 and 2026': '2024년 및 2026년 백화 전·최고 시기 비교',
    'Before / peak bleaching comparison': '백화 전·최고 시기 비교',
    'Alternative bleaching-comparison site': '대체 백화 비교 지역'
  };

  const koParts = [
    ['Before:', '백화 전:'],
    ['Peak:', '최고 시기:'],
    ['Baseline candidate:', '기준시기 후보:'],
    ['Bleaching-period candidate:', '백화시기 후보:'],
    ['Bleaching period:', '백화시기:'],
    ['Baseline:', '기준시기:'],
    ['Backups:', '예비 날짜:'],
    ['Sensitivity:', '민감도 검사:'],
    ['Timing checks:', '시기 민감도 검사:']
  ];

  const originals = new Map();
  const excluded = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEXTAREA', 'CODE']);
  let current = localStorage.getItem('inventoryLanguage') === 'ko' ? 'ko' : 'en';
  let observer;

  function translateDynamic(value) {
    if (ko[value]) return ko[value];
    for (const [english, korean] of koParts) {
      if (value.startsWith(english)) return korean + value.slice(english.length);
    }
    if (/^\d+ rows$/.test(value)) return value.replace(' rows', '개 행');
    if (/^\d+ candidates$/.test(value)) return value.replace(' candidates', '개 후보');
    if (/^\d+ scenes received$/i.test(value)) return value.replace(/scenes received/i, '개 영상 수령');
    if (/^\d{4}-\d{2}-\d{2} · \d+ scenes?$/.test(value)) return value.replace(/ · (\d+) scenes?$/, ' · $1개 영상');
    if (/^\d+% clear · GSD /.test(value)) return value.replace('% clear · GSD ', '% 맑음 · GSD ');
    if (/^[\d,]+ available local SAFE products$/.test(value)) return value.replace(' available local SAFE products', '개 로컬 SAFE 제품 보유');
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
    for (const [node] of originals) {
      if (!node.isConnected) originals.delete(node);
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
