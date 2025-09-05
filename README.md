# Backend
7팀 백엔드


### 1. 서비스 소개


### 2. 🚀 기술 스택
| Layer   | Stack | Notes |
| ------- | ----- | ----- |
| **Backend** | Django 5 · DRF | API 레이어, Serializer / Permission / Pagination |
| **Auth** | djangorestframework-simplejwt | 액세스·리프레시 토큰 발급, 만료 시각 ISO8601 표준 |
| **Storage** | AWS S3 · boto3 | Presigned **PUT** 업로드 & **GET** (프라이빗 시) |
| **Infra** | Nginx · Docker / docker-compose | 로컬 & 배포 환경 일관성 |
| **DB** | MySQL | 커스텀 User 모델(`user.User`) |
| **Web** | django-cors-headers | 프론트엔드 오리진 화이트리스트 관리 |

---

### 3. 👥 팀원 소개 (7팀)
| 이름   | 학교 | 포지션 |
| ------ | ---- | ------ |
| **강문정** | 연세 | 기획/디자인 |
| **우태호** | 연세 | 백엔드 |
| **백세빈** | 연세 | 백엔드 |
| **김연우** | 이화 | 백엔드 |
| **신지민** | 이화 | 백엔드 |
| **황영준** | 홍익 | 프론트엔드 |
| **장창엽** | 서강 | 프론트엔드 |
| **이윤서** | 홍익 | 프론트엔드 |

---

### 4. 📂 폴더 구조
```text
Backend/
└── sinchonApp/            # Django 프로젝트 루트
    ├── isscam/            # 사칭 관련 앱
    ├── similarity/        # 유사도 판별 앱
    ├── sinchonApp/        # 메인 설정 (settings.py 등)
    ├── storage/           # 스토리지/파일 관리 앱
    ├── user/              # 사용자 관리 앱
    └── wasscam/           # 와스캠(게시글/댓글/신고) 앱


### 5. 개발 환경에서의 실행 방법

   
### 6. 배포 링크
