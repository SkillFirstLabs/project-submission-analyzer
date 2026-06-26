// Mock data for the AI Project Submission Analyzer

export const DEFAULT_PROJECTS = [
  {
    id: 'nexus-core-migration',
    title: 'Project: Nexus Core Migration',
    rawTitle: 'Nexus Core Migration',
    description: 'An event-driven architectural migration for scale, separating monolithic notification services into specialized message-queue consumers using Apache Kafka and Redis caching layers.',
    outcomes: [
      'Implemented custom attention mechanism for event prioritisation',
      'Reduced message processing latency by 42%',
      'Achieved 99.9% delivery rate across 10m daily messages',
      'Configured automated fallback routing to dead-letter exchanges'
    ],
    architecture: 'Event-Driven Microservices',
    techStack: {
      frontend: ['React', 'Tailwind CSS', 'Framer Motion'],
      backend: ['Node.js', 'Express', 'Apache Kafka', 'Redis'],
      database: ['PostgreSQL', 'Mongoose'],
      devops: ['Docker', 'GitHub Actions']
    },
    dependencies: [
      { name: 'kafkajs', version: '^2.2.4', type: 'Production' },
      { name: 'redis', version: '^4.6.13', type: 'Production' },
      { name: 'express', version: '^4.19.2', type: 'Production' },
      { name: 'dotenv', version: '^16.4.5', type: 'Production' },
      { name: 'winston', version: '^3.12.0', type: 'Production' },
      { name: 'jest', version: '^29.7.0', type: 'Development' }
    ],
    files: [
      'package.json',
      'src/server.js',
      'src/config/kafka.js',
      'src/config/redis.js',
      'src/producers/notification.js',
      'src/consumers/emailConsumer.js',
      'src/consumers/smsConsumer.js',
      'src/services/cacheService.js',
      'src/utils/logger.js',
      'architecture.md',
      'docker-compose.yml',
      'tests/kafka.test.js'
    ],
    suggested_skills: [
      { skill_id: "sk-027", skill_name: "Redis", confidence: 0.95, rationale: "Used in caching layer and queue routing consumer." },
      { skill_id: "sk-016", skill_name: "Node.js", confidence: 0.88, rationale: "Powers backend consumer services and log interfaces." }
    ],
    confidence: 85,
    confidenceLabel: 'High Probability',
    authenticityScore: 78,
    authenticityBreakdown: {
      backend: 85,
      frontend: 60,
      database: 75,
      authentication: 70,
      businessLogic: 90,
      deployment: 80
    },
    indicators: {
      real: [
        'Custom Kafka consumer backpressure handler in emailConsumer.js',
        'Complex retry mechanism with exponential backoff and dead-letter queues',
        'Active telemetry logging hooked into Winston logger'
      ],
      missing: [
        'Complete end-to-end integration tests for Kafka partition rebalancing',
        'Production-grade secrets management (loaded purely from unencrypted .env)'
      ],
      superficial: [
        'Generic database helper files copied from boilerplate template projects',
        'Basic Dockerfile containing default Node.js alpine configurations'
      ],
      verdict: 'Highly authentic backend implementation. The candidate wrote core message consumer logic from scratch, though frontend dashboard indicators seem pre-templated or placeholder-based.'
    },
    audit: {
      strengths: [
        'Strong implementation of message queue backpressure.',
        'Well-designed retry strategy and dead-letter queue routing.',
        'Clean separation of consumer concerns.'
      ],
      weaknesses: [
        'Hardcoded fallback config variables in main producers.',
        'Absence of clustering support for memory-intensive routines.',
        'Weak coverage of unit tests for caching layers.'
      ],
      security: 'Environment variables are parsed directly. CORS parameters are loosely scoped in server.js. No token expiration checks implemented on webhook receivers.',
      architecture: 'Follows Publisher-Subscriber model using Kafka clusters. Separation of email and SMS handlers enables vertical scaling. Redis cache is bypassed during critical writes to maintain ACID compliance.',
      codeSmells: 'Complex callback chains in smsConsumer.js. Large monolithic configuration file in kafka.js.',
      technicalDebt: 'Outdated version of kafkajs used. Heavy reliance on global node processes instead of worker threads for secondary message formatting.',
      recommendations: 'Transition config variables to AWS Secrets Manager or HashiCorp Vault. Implement partitioning by client ID to parallelize delivery. Upgrade redis driver to latest stable release.'
    },
    questions: [
      {
        id: 1,
        question: 'Explain the specific architectural decisions behind using an Event-Driven approach for the notification microservice, rather than REST?',
        type: 'Conceptual',
        difficulty: 'Hard',
        timeLimit: 180, // seconds
        expectedPoints: [
          'Decoupling: Producers do not need to wait for consumer delivery confirmation, boosting write speeds.',
          'Scalability: Allows email and SMS consumers to scale independently under varying loads.',
          'Resilience: Message persistence in Kafka ensures delivery even if mail services temporarily fail.',
          'Backpressure management: Consumers pull messages at their own processing rate.'
        ],
        refFile: 'architecture.md',
        refLines: '45-52',
        suspicionText: 'Hesitation detected on architectural specifics. Probe deeper on line 45.'
      },
      {
        id: 2,
        question: 'In emailConsumer.js, how do you handle backpressure if the email SMTP provider starts rate-limiting your requests?',
        type: 'Codebase Specific',
        difficulty: 'Medium',
        timeLimit: 120,
        expectedPoints: [
          'Implemented consumer.pause() to halt fetching from Kafka partition.',
          'Utilised setTimeout delay loop with exponential backoff before sending health check request.',
          'Invoked consumer.resume() once delivery confirmation metrics return to nominal range.',
          'Redirected persistent failed sends to Dead Letter Queue (DLQ) after 3 retries.'
        ],
        refFile: 'src/consumers/emailConsumer.js',
        refLines: '84-105',
        suspicionText: 'Looked away from screen. Quick browser window focus change detected.'
      },
      {
        id: 3,
        question: 'What mechanism ensures that messages are distributed evenly across your Kafka partitions, and why is order important here?',
        type: 'Conceptual',
        difficulty: 'Hard',
        timeLimit: 150,
        expectedPoints: [
          'Message keying: Partition keys based on userId ensure single-user messages route to the same partition.',
          'Strict sequencing: Ensures notification events (e.g. Account Created before Welcome Email) process in order.',
          'Round-robin fallback: Default partitioner distributes load evenly when keys are null.'
        ],
        refFile: 'src/producers/notification.js',
        refLines: '24-38',
        suspicionText: 'Clear, rapid response. Demonstrates high confidence.'
      },
      {
        id: 4,
        question: 'Why did you bypass Redis caching when registering webhook callbacks, and how does that affect database integrity?',
        type: 'Codebase Specific',
        difficulty: 'Medium',
        timeLimit: 120,
        expectedPoints: [
          'Ensures write-through data consistency to PostgreSQL repository.',
          'Avoids race conditions where stale cache values serve webhook configurations.',
          'Accepts a small performance trade-off to ensure 100% accurate callback URL resolutions.'
        ],
        refFile: 'src/services/cacheService.js',
        refLines: '110-128',
        suspicionText: 'Long pause before answering. Possible reference of external notes.'
      },
      {
        id: 5,
        question: 'How does your Docker Compose configuration handle networking between the local Kafka broker, Zookeeper, and the Node application?',
        type: 'Codebase Specific',
        difficulty: 'Easy',
        timeLimit: 90,
        expectedPoints: [
          'Uses a bridge network named custom_network.',
          'Exposes internal ports 9092 for inter-container communication and 29092 for localhost binding.',
          'Uses depends_on configuration to delay application startup until Kafka reports healthy.'
        ],
        refFile: 'docker-compose.yml',
        refLines: '12-32',
        suspicionText: 'High confidence. Familiarity with local deployment scripts.'
      }
    ]
  },
  {
    id: 'neural-network-optimizer',
    title: 'Project: Neural Network Optimizer',
    rawTitle: 'Neural Network Optimizer',
    description: 'A performance tuning module that compiles neural model hyperparameters and uses custom attention networks to compress visual processing pipelines by up to 40%.',
    outcomes: [
      'Implemented custom attention mechanism',
      'Reduced inference latency by 40%',
      'Achieved 95% accuracy on test set'
    ],
    architecture: 'Model Optimization Pipeline',
    techStack: {
      frontend: ['React', 'Recharts'],
      backend: ['FastAPI', 'PyTorch', 'NumPy'],
      database: ['SQLite'],
      devops: ['Docker']
    },
    dependencies: [
      { name: 'torch', version: '^2.1.2', type: 'Production' },
      { name: 'numpy', version: '^1.26.2', type: 'Production' },
      { name: 'fastapi', version: '^0.104.1', type: 'Production' },
      { name: 'uvicorn', version: '^0.24.0', type: 'Production' }
    ],
    files: [
      'main.py',
      'model/attention.py',
      'model/optimizer.py',
      'utils/dataset.py',
      'requirements.txt',
      'Dockerfile',
      'README.md'
    ],
    suggested_skills: [
      { skill_id: "sk-046", skill_name: "PyTorch", confidence: 0.95, rationale: "Custom attention network and tensor operations." },
      { skill_id: "sk-044", skill_name: "NumPy", confidence: 0.90, rationale: "Optimized array transformations and CUDA allocations." }
    ],
    confidence: 94,
    confidenceLabel: 'Very High Probability',
    authenticityScore: 89,
    authenticityBreakdown: {
      backend: 95,
      frontend: 70,
      database: 60,
      authentication: 50,
      businessLogic: 98,
      deployment: 85
    },
    indicators: {
      real: [
        'Custom multi-head attention matrix multiplication in attention.py',
        'Optimized matrix slicing logic in NumPy avoiding memory allocations',
        'Configured PyTorch CUDA core allocations manually'
      ],
      missing: [
        'Multi-GPU node training config (currently single node only)',
        'Authentication layer on FastAPI server'
      ],
      superficial: [
        'Visual evaluation React dashboard uses static placeholder arrays',
        'Standard PyTorch weight loading paths from local system file paths'
      ],
      verdict: 'Extremely authentic numerical analysis project. The attention layers are hand-crafted, showing deep mathematical proficiency.'
    },
    audit: {
      strengths: [
        'Highly efficient tensor multiplication routines.',
        'Proper CUDA resource releasing, preventing memory leaks.',
        'Clean implementation of attention weights.'
      ],
      weaknesses: [
        'Lacks cross-platform model export options like ONNX.',
        'No rate limiting on endpoint inputs.',
        'Hardcoded batch parameters in training script.'
      ],
      security: 'FastAPI validation handles SQL injection checks but fails to authenticate API tokens. Local files loaded without path validation.',
      architecture: 'Pipeline structure with lazy loader. Numerical tasks are separated from routing thread loops using asynchronous workers.',
      codeSmells: 'Deeply nested loop inside optimizer.py during convergence checking.',
      technicalDebt: 'Relies on legacy NumPy syntax for array declarations. Lacks static type checking files.',
      recommendations: 'Integrate dynamic batch sizes. Port matrices to Triton or C++ bindings. Introduce JWT tokens for FastAPI endpoints.'
    },
    questions: [
      {
        id: 1,
        question: 'Describe the mathematical formulation of your custom attention mechanism, and why it cuts down visual latency.',
        type: 'Conceptual',
        difficulty: 'Hard',
        timeLimit: 180,
        expectedPoints: [
          'Calculates Query, Key, and Value matrices from input visual tensors.',
          'Applies Scaled Dot-Product Attention: Softmax(QK^T / sqrt(d_k))V.',
          'Dimensionality reduction: Reduces key/value dimensions prior to scaling, preserving spatial representations.',
          'Memory optimization: Parallelizes matrix products using unified CPU/GPU shared cache.'
        ],
        refFile: 'model/attention.py',
        refLines: '15-34',
        suspicionText: 'Very confident, answered mathematical queries instantly.'
      },
      {
        id: 2,
        question: 'Why did you use PyTorch raw tensor manipulation rather than pre-built nn.MultiheadAttention modules?',
        type: 'Codebase Specific',
        difficulty: 'Medium',
        timeLimit: 120,
        expectedPoints: [
          'Requires custom mask weights applied at sub-layer levels.',
          'Pre-built libraries do not expose intermediate attention scores needed for compression ratios.',
          'Optimized compilation constraints that fit specific edge hardware targets.'
        ],
        refFile: 'model/attention.py',
        refLines: '38-55',
        suspicionText: 'Minor stutter. Recovered with detailed explanation of compilation flags.'
      },
      {
        id: 3,
        question: 'How do you prevent CUDA out-of-memory errors during evaluation runs with large batch sizes?',
        type: 'Codebase Specific',
        difficulty: 'Medium',
        timeLimit: 120,
        expectedPoints: [
          'Wrapped verification routines in torch.no_grad() context manager.',
          'Used torch.cuda.empty_cache() explicitly after completing step blocks.',
          'Implemented gradient accumulation to simulate large batches with small footprints.'
        ],
        refFile: 'model/optimizer.py',
        refLines: '72-91',
        suspicionText: 'Eye movements indicate reading another window. Slight delay.'
      }
    ]
  }
];

export const MOCK_LOGS = [
  'Initializing workspace extraction...',
  'Extracting source code repository structure...',
  'Processing package configuration metrics...',
  'Detected package manager: npm (package.json present)',
  'Analyzing dependencies list...',
  'Found 6 production packages, 5 development packages',
  'Analyzing source code files (12 items identified)...',
  'Parsing files structure and imports trees...',
  'Computing complexity metrics...',
  'Detected programming languages: JavaScript (84%), Markdown (10%), YAML (6%)',
  'Analyzing design structure and architecture components...',
  'Evidence identified: Event-Driven Consumers, Kafka Message Bus configuration',
  'Verifying outcomes and evidence links...',
  'Met: Custom attention priority validation found in emailConsumer.js:L84',
  'Met: Delivery latency logs discovered in winston config tests/kafka.test.js:L12',
  'Performing project authenticity checks...',
  'Authenticity score: 78% based on coding style match and repository history',
  'Identifying code duplicates and boilerplate imports...',
  'Generating viva examination questionnaire...',
  'Questionnaire set: 5 items configured based on technical depth requirements',
  'Preparing evaluation dashboard data...',
  'Analysis complete. Visual reports ready.'
];
