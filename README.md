# Product-Importer
product-importer/
├── README.md                      # Main documentation
├── DEPLOYMENT.md                  # Deployment guide
├── AI_PROMPTS.md                  # AI tools usage log
├── requirements.txt               # Python dependencies
├── main.py                        # FastAPI + Celery app
├── Dockerfile                     # Container config
├── docker-compose.yml             # Local dev setup
├── Procfile                       # Heroku config
├── render.yaml                    # Render.com blueprint
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── frontend/
│   └── index.html                # React UI
├── tests/
│   ├── generate_test_csv.py      # Test data generator
│   ├── test_api.py               # API test suite
│   ├── performance_test.py       # Load testing
│   └── webhook_test_server.py    # Webhook tester
└── samples/
    ├── small_test.csv            # 100 products
    ├── medium_test.csv           # 10K products
    └── large_test.csv            # 100K products
