import re
from typing import Any, Dict, List, Optional

from backend.grader.star_grader import STARGrader


class TestHarness:

    def load_test_data(self) -> List[Dict[str, Any]]:
        tc: List[Dict[str, Any]] = []
        idx = 1

        technical_good = [
            {
                "question": "Can you describe a time you optimized a database query that was causing performance issues?",
                "answer": (
                    "Situation: At my previous company, our main customer dashboard was taking over 12 seconds to load, "
                    "and the support team was getting hundreds of complaints daily. I investigated and found the root cause "
                    "in our PostgreSQL database layer.\n\n"
                    "Task: My manager asked me to reduce the dashboard load time to under 3 seconds within two sprints.\n\n"
                    "Action: I used EXPLAIN ANALYZE to identify a missing composite index on the users and orders tables. "
                    "I created a composite index on (user_id, created_at DESC), rewrote three N+1 queries into single "
                    "JOINs, added read replicas for analytics queries, and implemented Redis caching for the top 1000 "
                    "active users' dashboards.\n\n"
                    "Result: Dashboard load time dropped from 12 seconds to 1.8 seconds. Support tickets related to "
                    "performance decreased by 94%. The solution saved an estimated 200 engineering hours per quarter "
                    "previously spent on performance firefighting."
                ),
                "job_context": "Senior Backend Engineer: PostgreSQL, query optimization, Redis caching, performance tuning",
                "expected_score": 9,
            },
            {
                "question": "Tell me about a project where you implemented a microservices architecture.",
                "answer": (
                    "Situation: Our monolithic e-commerce application was hitting scaling limits during flash sales, "
                    "with the entire system crashing when one module overloaded.\n\n"
                    "Task: I was tasked with decomposing the monolith into microservices for the checkout, inventory, "
                    "and payment modules.\n\n"
                    "Action: I designed service boundaries using domain-driven design principles. I implemented each "
                    "service using Go with gRPC for inter-service communication. I set up Kubernetes for orchestration, "
                    "Prometheus for monitoring, and implemented circuit breakers with Istio. Each service had its own "
                    "PostgreSQL database following the database-per-service pattern.\n\n"
                    "Result: The system handled 10x the traffic during the next flash sale with zero downtime. "
                    "Deployment frequency increased from bi-weekly to multiple times per day per service. Mean time "
                    "to recovery dropped from 45 minutes to under 5 minutes."
                ),
                "job_context": "Staff Engineer: microservices, Kubernetes, Go, gRPC, distributed systems",
                "expected_score": 9,
            },
            {
                "question": "How do you approach code reviews in your team?",
                "answer": (
                    "Situation: Our team of 8 engineers was shipping features rapidly but accumulating technical debt "
                    "and introducing bugs that reached production.\n\n"
                    "Task: I wanted to establish a code review culture that improved code quality without slowing "
                    "down velocity.\n\n"
                    "Action: I introduced a lightweight review checklist covering security, performance, test coverage, "
                    "and readability. I set up GitHub branch protection rules requiring at least one approval. I created "
                    "a Slack channel for discussing tricky reviews asynchronously. I also started weekly review pairing "
                    "sessions where junior and senior engineers reviewed code together.\n\n"
                    "Result: Production bugs decreased by 60% over three months. Junior engineers' code quality scores "
                    "improved significantly. The team's velocity actually increased by 15% because we spent less time "
                    "on bug fixes."
                ),
                "job_context": "Tech Lead: code review, team leadership, quality assurance, mentoring",
                "expected_score": 8,
            },
            {
                "question": "Describe your experience with CI/CD pipelines.",
                "answer": (
                    "Situation: Our deployment process was manual, involving SSH into servers, pulling code, and "
                    "restarting services. This caused frequent deployment errors and made rollbacks nearly impossible.\n\n"
                    "Task: I needed to automate our entire build, test, and deployment pipeline for a Python/Django "
                    "application serving 500K daily active users.\n\n"
                    "Action: I built a Jenkins pipeline with stages for linting (flake8, mypy), unit tests (pytest with "
                    "85% coverage threshold), integration tests against a test database, Docker image building, "
                    "security scanning with Trivy, and blue-green deployment to AWS ECS. I implemented automatic "
                    "rollback triggers based on CloudWatch error rate alarms.\n\n"
                    "Result: Deployment time went from 2 hours to 12 minutes. Failed deployments dropped from 15% "
                    "to less than 2%. Rollback time went from 45 minutes to under 90 seconds. The team deployed "
                    "300% more frequently."
                ),
                "job_context": "DevOps Engineer: CI/CD, Jenkins, AWS ECS, Docker, automated testing",
                "expected_score": 9,
            },
        ]

        technical_bad = [
            {
                "question": "Can you describe a time you optimized a database query?",
                "answer": "Yeah I fixed some slow queries at work. It was pretty straightforward, just added some indexes and it was faster. The users were happy about it.",
                "job_context": "Senior Backend Engineer: PostgreSQL, query optimization, Redis caching, performance tuning",
                "expected_score": 3,
            },
            {
                "question": "Tell me about a project where you implemented microservices.",
                "answer": "I used microservices at my last job. It was a big project with lots of services talking to each other. We used Docker and Kubernetes. It worked out well in the end and the system was more scalable.",
                "job_context": "Staff Engineer: microservices, Kubernetes, Go, gRPC, distributed systems",
                "expected_score": 3,
            },
            {
                "question": "How do you approach code reviews?",
                "answer": "I look at the code and if it looks good I approve it. Sometimes I leave comments if I see obvious issues. I think code reviews are important for catching bugs.",
                "job_context": "Tech Lead: code review, team leadership, quality assurance, mentoring",
                "expected_score": 2,
            },
            {
                "question": "Describe your experience with CI/CD pipelines.",
                "answer": "I have used Jenkins before for deploying code. It was set up by someone else and I just ran the builds when needed. I know it automates things but I did not configure it myself.",
                "job_context": "DevOps Engineer: CI/CD, Jenkins, AWS ECS, Docker, automated testing",
                "expected_score": 3,
            },
        ]
        for item in technical_good + technical_bad:
            tc.append({"id": idx, "category": "technical", **item})
            idx += 1

        behavioral_good = [
            {
                "question": "Tell me about a time you had a conflict with a coworker and how you resolved it.",
                "answer": (
                    "Situation: A senior engineer on my team strongly disagreed with my proposed approach to refactoring "
                    "our authentication system. He wanted to rewrite everything while I advocated for an incremental "
                    "migration. The tension was affecting the whole team's morale.\n\n"
                    "Task: I needed to resolve this disagreement constructively while maintaining our working relationship "
                    "and ensuring we chose the best technical approach.\n\n"
                    "Action: I invited him for a coffee and listened to his concerns fully before sharing mine. I "
                    "proposed we each write a one-page design doc with risk analysis and present both to the team. "
                    "I also suggested a compromise: incremental migration with clear module boundaries that could "
                    "eventually become a full rewrite if needed.\n\n"
                    "Result: He appreciated being heard and agreed the compromise was sound. The team voted and chose "
                    "my approach. We completed the migration in 6 weeks with zero downtime. Our relationship improved "
                    "significantly and we ended up co-authoring a blog post about our migration strategy."
                ),
                "job_context": "Senior Engineer: teamwork, conflict resolution, communication, technical decision-making",
                "expected_score": 9,
            },
            {
                "question": "Describe a situation where you went above and beyond your role.",
                "answer": (
                    "Situation: Our startup was two weeks from a critical investor demo and the mobile app's login flow "
                    "had a critical bug that the mobile team could not reproduce in their environment.\n\n"
                    "Task: I was a backend engineer, but the bug appeared to be in the OAuth token exchange between "
                    "our backend and the mobile app. No one else had context on both sides.\n\n"
                    "Action: I spent three evenings reproducing the issue, setting up the mobile dev environment on my "
                    "machine, and tracing the token flow end-to-end. I discovered a race condition in the refresh token "
                    "logic. I fixed the backend, wrote a detailed postmortem, and created runbooks so the team could "
            "handle similar issues.\n\n"
                    "Result: The demo went perfectly. The investor signed a $2M term sheet. My manager highlighted my "
                    "initiative in the all-hands meeting and I was promoted to senior engineer the following quarter."
                ),
                "job_context": "Senior Engineer: initiative, cross-functional collaboration, problem ownership",
                "expected_score": 9,
            },
            {
                "question": "Tell me about a time you received critical feedback.",
                "answer": (
                    "Situation: During my mid-year review, my manager told me that while my technical skills were "
                    "strong, I tended to dominate technical discussions and not give quieter team members enough space "
                    "to contribute.\n\n"
                    "Task: I needed to improve my meeting facilitation and make sure all voices were heard during "
                    "technical discussions.\n\n"
                    "Action: I started using a round-robin approach in design reviews where each person shared their "
                    "thoughts before open discussion. I practiced active listening and asked specific questions to "
                    "quieter members like 'Priya, what's your take on this approach?' I also read 'The Coaching Habit' "
                    "and applied its questioning techniques.\n\n"
                    "Result: In the next review cycle, three team members specifically mentioned feeling more included. "
                    "Our design docs improved because we captured more diverse perspectives. My manager noted the "
                    "tangible improvement and I was asked to mentor two new team leads."
                ),
                "job_context": "Team Lead: self-improvement, feedback reception, inclusive leadership",
                "expected_score": 8,
            },
            {
                "question": "Describe how you handle tight deadlines.",
                "answer": (
                    "Situation: Our e-commerce platform had a critical security vulnerability disclosed publicly, "
                    "and we had 48 hours before the deadline for PCI compliance audit.\n\n"
                    "Task: I needed to implement rate limiting, input sanitization, and security headers across "
                    "15 microservices within 48 hours.\n\n"
                    "Action: I immediately triaged the work into must-have and nice-to-have. I set up a war room "
                    "with the security and DevOps teams. I created an API gateway layer with rate limiting in NGINX, "
                    "built a shared security middleware library, and delegated implementation of individual services "
                    "to team members while I handled the most complex payment service myself. We did continuous "
                    "deployment with 2-hour check-ins.\n\n"
                    "Result: All 15 services were patched within 36 hours. We passed the PCI audit with no findings. "
                    "The shared security middleware became a reusable component that prevented similar vulnerabilities "
                    "in future services."
                ),
                "job_context": "Senior Engineer: deadline management, security, triage, cross-team coordination",
                "expected_score": 9,
            },
        ]

        behavioral_bad = [
            {
                "question": "Tell me about a time you had a conflict with a coworker.",
                "answer": "I had a coworker who was annoying and kept disagreeing with me. I told my manager about it and they handled it. After that things were better.",
                "job_context": "Senior Engineer: teamwork, conflict resolution, communication, technical decision-making",
                "expected_score": 2,
            },
            {
                "question": "Describe a situation where you went above and beyond.",
                "answer": "I always work hard and do my best. I stay late sometimes when there is a lot of work. I think that shows dedication to the job.",
                "job_context": "Senior Engineer: initiative, cross-functional collaboration, problem ownership",
                "expected_score": 3,
            },
            {
                "question": "Tell me about a time you received critical feedback.",
                "answer": "I do not really get critical feedback because I do good work. My managers always say I am doing a great job. I cannot think of a specific time.",
                "job_context": "Team Lead: self-improvement, feedback reception, inclusive leadership",
                "expected_score": 2,
            },
            {
                "question": "Describe how you handle tight deadlines.",
                "answer": "I just work harder when deadlines are tight. I stay late and do whatever it takes. I do not really have a specific process, I just push through it.",
                "job_context": "Senior Engineer: deadline management, security, triage, cross-team coordination",
                "expected_score": 3,
            },
        ]
        for item in behavioral_good + behavioral_bad:
            tc.append({"id": idx, "category": "behavioral", **item})
            idx += 1

        experience_good = [
            {
                "question": "Walk me through your most complex project and your role in it.",
                "answer": (
                    "Situation: I joined a fintech startup building a real-time fraud detection system processing "
                    "2 million transactions per day with a team of 4 engineers.\n\n"
                    "Task: I was responsible for designing the streaming data pipeline and the real-time scoring engine "
                    "that needed to detect fraud in under 50 milliseconds.\n\n"
                    "Action: I architected an Apache Kafka-based streaming pipeline with Apache Flink for real-time "
                    "feature computation. I implemented a gradient boosting model in XGBoost that combined real-time "
                    "features with historical patterns. I built a feature store using Redis for low-latency lookups, "
                    "set up a shadow scoring pipeline for A/B testing, and created a real-time dashboard for the fraud "
                    "team using Grafana.\n\n"
                    "Result: The system detected fraud 3x faster than the previous batch-based approach, reducing "
                    "fraud losses by $4.2M annually. False positive rate dropped from 8% to 2.3%. The system processed "
                    "peak loads of 5,000 TPS with p99 latency under 40ms."
                ),
                "job_context": "Senior Data Engineer: Kafka, Flink, real-time systems, data pipelines, fintech",
                "expected_score": 9,
            },
            {
                "question": "What is the largest system you have designed from scratch?",
                "answer": (
                    "Situation: I was asked to design a notification platform for a company with 10M registered users "
                    "across web, mobile, and email channels.\n\n"
                    "Task: Design a scalable, reliable notification system that supports templating, scheduling, "
                    "user preferences, and delivery tracking across multiple channels.\n\n"
                    "Action: I designed a microservices architecture with separate services for template management, "
                    "preference management, routing, and delivery. I used Kafka for async processing, PostgreSQL "
                    "for user preferences, DynamoDB for template storage, and SQS for dead letter queues. I implemented "
                    "a priority queue system for urgent notifications and a rate limiter to prevent notification fatigue. "
                    "I designed the system for exactly-once delivery using idempotency keys.\n\n"
                    "Result: The platform handled 500K notifications per minute at peak. Delivery rate reached 99.7%. "
                    "User opt-out rates decreased by 35% due to the preference system. The platform was adopted by "
                    "3 product teams within the first quarter."
                ),
                "job_context": "Principal Engineer: system design, distributed systems, architecture, scalability",
                "expected_score": 9,
            },
            {
                "question": "How has your experience prepared you for this role?",
                "answer": (
                    "Situation: Over my 8 years of software engineering, I have progressively taken on larger scope "
                    "roles from individual contributor to tech lead managing a team of 12.\n\n"
                    "Task: I am looking for a role where I can combine deep technical expertise with people leadership "
                    "at a company solving challenging distributed systems problems.\n\n"
                    "Action: At my current company, I led the migration from a monolith to microservices serving 50M "
                    "users. I built and mentored a team of 12 engineers, establishing engineering practices that "
                    "improved deployment frequency by 400%. I also established the company's first architecture review "
                    "board and created an internal engineering blog that became a recruiting asset.\n\n"
                    "Result: My team consistently exceeded OKRs. Three of my direct reports were promoted to senior "
                    "engineer. The architecture I designed has scaled to 3x the original user base with minimal changes. "
                    "I believe this combination of hands-on technical leadership and team building directly maps to "
                    "the requirements of this role."
                ),
                "job_context": "Engineering Manager: leadership, architecture, team building, scaling systems",
                "expected_score": 8,
            },
            {
                "question": "Describe your experience with cloud infrastructure at scale.",
                "answer": (
                    "Situation: Our company was migrating from on-premises data centers to AWS, involving 200+ servers "
                    "and 50+ applications.\n\n"
                    "Task: I led the cloud migration initiative, responsible for architecture decisions, cost "
                    "optimization, and ensuring zero downtime during the transition.\n\n"
                    "Action: I created a migration framework categorizing apps as rehost, replatform, or refactor. "
                    "I implemented Terraform for infrastructure-as-code, EKS for containerized workloads, and "
                    "AWS Lambda for event-driven services. I built a FinOps dashboard using AWS Cost Explorer APIs "
                    "and implemented spot instances for non-critical workloads. I established guardrails with AWS "
                    "Config rules and Service Control Policies.\n\n"
                    "Result: Migration completed 2 months ahead of schedule and 15% under budget. Annual cloud costs "
                    "were $1.2M lower than projected thanks to spot instances and right-sizing. Infrastructure "
                    "provisioning went from 2 weeks to 15 minutes. The company achieved SOC 2 compliance on AWS "
                    "within 3 months."
                ),
                "job_context": "Cloud Architect: AWS, Terraform, EKS, migration, FinOps",
                "expected_score": 9,
            },
        ]

        experience_bad = [
            {
                "question": "Walk me through your most complex project.",
                "answer": "I worked on a big project at my last job. It was a web application with a frontend and backend. I did both. It took about 6 months and we launched it on time. The client was happy.",
                "job_context": "Senior Data Engineer: Kafka, Flink, real-time systems, data pipelines, fintech",
                "expected_score": 3,
            },
            {
                "question": "What is the largest system you have designed?",
                "answer": "I designed some systems at work. I used common patterns and technologies. It was a typical CRUD application with a database. Nothing too unusual.",
                "job_context": "Principal Engineer: system design, distributed systems, architecture, scalability",
                "expected_score": 2,
            },
            {
                "question": "How has your experience prepared you for this role?",
                "answer": "I have been working as a developer for a few years. I have experience with various technologies. I think I am a good fit for this position because I am a hard worker and a quick learner.",
                "job_context": "Engineering Manager: leadership, architecture, team building, scaling systems",
                "expected_score": 3,
            },
            {
                "question": "Describe your experience with cloud infrastructure.",
                "answer": "I have used AWS a little bit. I have launched EC2 instances and S3 buckets. I know the basics of cloud computing. I am eager to learn more about cloud infrastructure.",
                "job_context": "Cloud Architect: AWS, Terraform, EKS, migration, FinOps",
                "expected_score": 2,
            },
        ]
        for item in experience_good + experience_bad:
            tc.append({"id": idx, "category": "experience", **item})
            idx += 1

        problem_solving_good = [
            {
                "question": "How would you debug a production outage affecting 30% of users?",
                "answer": (
                    "Situation: At 2 AM, our monitoring alerts fired showing 30% of users getting 500 errors on "
                    "our checkout API. The on-call engineer escalated to me as the incident commander.\n\n"
                    "Task: I needed to restore service quickly while diagnosing root cause and ensuring no data loss.\n\n"
                    "Action: I immediately set up a war room with the relevant engineers. I checked dashboards: error "
                    "rates were spiking on the payment service. I traced the issue to a deployment 30 minutes earlier "
                    "that introduced a schema change. I coordinated a rollback of the specific deployment using our "
                    "blue-green setup. While the rollback propagated, I checked transaction logs to confirm no "
                    "payment data was corrupted. I set up a Redis read-through cache as a temporary shield.\n\n"
                    "Result: Full service restored in 12 minutes. No payment data was lost or duplicated. I wrote "
                    "a postmortem and added a schema validation step to the CI pipeline that would have caught the "
                    "breaking change. I also implemented automated rollback triggers based on error rate thresholds."
                ),
                "job_context": "SRE: incident response, debugging, production systems, postmortems, reliability",
                "expected_score": 9,
            },
            {
                "question": "You discover your application has a memory leak in production. How do you approach this?",
                "answer": (
                    "Situation: Our Node.js application's memory usage was growing steadily, causing OOM kills "
                    "every 6-8 hours and requiring manual restarts.\n\n"
                    "Task: Identify the root cause of the memory leak and implement a fix without disrupting service.\n\n"
                    "Action: I attached a heap profiler using clinic.js and collected snapshots over a 2-hour window. "
                    "I compared heap snapshots and found event listeners accumulating on a WebSocket connection handler. "
                    "Each reconnection was adding new listeners without cleaning up old ones. I fixed the listener "
                    "cleanup in the disconnect handler, added a max listener count warning, and implemented a "
                    "connection pool with proper resource management. I also added memory usage alerts at 70% and "
                    "85% thresholds.\n\n"
                    "Result: Memory usage stabilized at 200MB instead of growing to 2GB. OOM kills dropped to zero. "
                    "The fix was deployed with zero downtime. The memory alerts have caught two other potential "
                    "leaks before they became production issues."
                ),
                "job_context": "Backend Engineer: Node.js, debugging, memory profiling, production reliability",
                "expected_score": 9,
            },
            {
                "question": "Describe how you would design a solution for real-time collaborative editing.",
                "answer": (
                    "Situation: We were building a collaborative document editor similar to Google Docs and needed "
                    "to support 50+ concurrent editors per document with sub-100ms sync latency.\n\n"
                    "Task: Design the conflict resolution and real-time synchronization architecture.\n\n"
                    "Action: I researched CRDTs vs OT algorithms and chose Yjs CRDTs for their simplicity and "
                    "offline-first capability. I implemented a WebSocket server using uWebSockets.js for high "
                    "performance, with Redis Pub/Sub for multi-server sync. I built a persistence layer that "
                    "periodically snapshots the CRDT state to PostgreSQL. I implemented awareness protocol for "
                    "cursors and selections. For the edge case of network partitions, I used CRDTs' inherent "
                    "conflict resolution.\n\n"
                    "Result: The system supported 75 concurrent editors with 40ms average sync latency. Conflict "
                    "resolution was seamless with zero data loss during network partitions. The system handled "
                    "500 documents simultaneously with stable memory usage."
                ),
                "job_context": "Senior Engineer: distributed systems, CRDTs, WebSockets, real-time collaboration",
                "expected_score": 9,
            },
            {
                "question": "How would you approach reducing API response times from 2 seconds to under 200ms?",
                "answer": (
                    "Situation: Our main API endpoint was averaging 2 seconds response time, causing user "
                    "complaints and mobile app abandonment.\n\n"
                    "Task: Reduce p95 latency to under 200ms without major architectural changes.\n\n"
                    "Action: I started by adding OpenTelemetry tracing to identify bottlenecks. I found 60% of the "
                    "time was in 3 sequential database queries. I added strategic caching with Redis for the most "
                    "frequently accessed data. I parallelized the remaining queries using asyncio. I added a "
                    "read-through cache with stale-while-revalidate for the product catalog. I also added a CDN "
                    "layer for static API responses and implemented GraphQL dataloader patterns.\n\n"
                    "Result: p95 latency dropped from 2.1s to 140ms. Cache hit rate reached 85%. Database load "
                    "decreased by 70%. User engagement metrics improved by 25% on mobile."
                ),
                "job_context": "Backend Engineer: performance optimization, caching, API design, observability",
                "expected_score": 8,
            },
        ]

        problem_solving_bad = [
            {
                "question": "How would you debug a production outage?",
                "answer": "I would check the logs and see what the error is. Then I would try to fix it. If I cannot fix it, I would ask for help from my team. Usually restarting the server helps.",
                "job_context": "SRE: incident response, debugging, production systems, postmortems, reliability",
                "expected_score": 3,
            },
            {
                "question": "You discover a memory leak. How do you approach this?",
                "answer": "Memory leaks are annoying. I would probably restart the server and see if it happens again. If it does, I might look at the code to find the issue. I have not dealt with memory leaks much.",
                "job_context": "Backend Engineer: Node.js, debugging, memory profiling, production reliability",
                "expected_score": 2,
            },
            {
                "question": "How would you design real-time collaborative editing?",
                "answer": "I would use WebSockets and a database. When someone types something, send it to the server and then broadcast to everyone. For conflicts, I would just lock the document for other users when one person is editing.",
                "job_context": "Senior Engineer: distributed systems, CRDTs, WebSockets, real-time collaboration",
                "expected_score": 3,
            },
            {
                "question": "How would you reduce API response times?",
                "answer": "I would add more servers to handle the load. Maybe upgrade the hardware. Caching could help too. I have not done much performance optimization work specifically.",
                "job_context": "Backend Engineer: performance optimization, caching, API design, observability",
                "expected_score": 2,
            },
        ]
        for item in problem_solving_good + problem_solving_bad:
            tc.append({"id": idx, "category": "problem_solving", **item})
            idx += 1

        leadership_good = [
            {
                "question": "How do you handle underperforming team members?",
                "answer": (
                    "Situation: One of my engineers was consistently missing deadlines and producing code that needed "
                    "significant rework. This was affecting the whole team's sprint commitments.\n\n"
                    "Task: I needed to address the performance issue compassionately while ensuring team output "
                    "and supporting the individual's growth.\n\n"
                    "Action: I scheduled a private 1:1 and asked open-ended questions to understand root causes. "
                    "I learned they were dealing with unclear requirements and struggling with a new technology stack. "
                    "I created a structured 30-60-90 day improvement plan with clear, measurable goals. I paired "
                    "them with a senior mentor for the technology gap. I also improved our requirement documentation "
                    "process for the whole team.\n\n"
                    "Result: Within 60 days, their velocity improved by 50%. Their code review pass rate went from "
                    "60% to 90%. They later became the team's expert on the new technology stack. The improved "
                    "requirement process benefited all new team members joining subsequently."
                ),
                "job_context": "Engineering Manager: people management, performance improvement, mentoring",
                "expected_score": 9,
            },
            {
                "question": "Describe how you have driven technical strategy in your organization.",
                "answer": (
                    "Situation: Our engineering organization of 80 engineers had no shared technical standards. "
                    "Teams were using different frameworks, databases, and deployment patterns, creating significant "
                    "integration friction.\n\n"
                    "Task: I proposed and led an initiative to establish an engineering-wide technical strategy "
                    "and governance framework.\n\n"
                    "Action: I formed a cross-team Architecture Guild with representatives from each team. I created "
                    "an RFC process for significant technical decisions. I authored proposals for our standard "
                    "technology stack, observability practices, and API design guidelines. I organized monthly "
                    "tech talks and built an internal knowledge base. I presented the strategy to engineering "
                    "leadership with cost-benefit analysis and got buy-in from VP of Engineering.\n\n"
                    "Result: Cross-team integration time decreased by 40%. New engineer onboarding time dropped "
                    "from 6 weeks to 3 weeks. The RFC process prevented 3 costly architectural mistakes. "
                    "The Architecture Guild became self-sustaining and continued driving standards after my "
                    "initial term."
                ),
                "job_context": "Staff Engineer: technical strategy, architecture governance, organizational leadership",
                "expected_score": 9,
            },
            {
                "question": "How do you prioritize competing technical priorities?",
                "answer": (
                    "Situation: As tech lead, I was managing three competing priorities: a critical security fix, "
                    "a feature for a major client deadline in 2 weeks, and technical debt that was causing "
                    "weekly deployment failures.\n\n"
                    "Task: Allocate a team of 6 engineers across these priorities while meeting all commitments.\n\n"
                    "Action: I created an impact vs effort matrix and scored each priority. The security fix was "
                    "high impact, low effort, so I assigned 2 engineers for immediate resolution. For the client "
                    "feature, I assigned 3 engineers and broke the feature into MVP scope to meet the deadline. "
                    "For tech debt, I assigned 1 engineer to fix the deployment pipeline issues. I communicated "
                    "the plan and rationale to all stakeholders, including the client, with clear timelines.\n\n"
                    "Result: Security fix deployed in 3 days. Client feature shipped on time with MVP scope and "
                    "remaining polish delivered 1 week later. Deployment failures reduced by 80%. All three "
                    "stakeholders were satisfied with the outcomes. The prioritization framework became a template "
                    "the team used for future decisions."
                ),
                "job_context": "Tech Lead: prioritization, stakeholder management, resource allocation",
                "expected_score": 9,
            },
            {
                "question": "Tell me about a time you had to influence without authority.",
                "answer": (
                    "Situation: I noticed our platform was accumulating significant technical debt in error handling, "
                    "but the product team kept prioritizing features. Incidents were increasing by 30% quarter over "
                    "quarter.\n\n"
                    "Task: Convince product leadership to allocate engineering capacity to reliability improvements "
                    "without formal authority over the roadmap.\n\n"
                    "Action: I built a data-driven business case: tracked every incident, quantified engineering time "
                    "lost to firefighting ($340K/quarter), and correlated reliability metrics with customer churn. "
                    "I presented this at the all-hands meeting with customer quotes about outages. I proposed a "
                    "20% reliability allocation model, showing the ROI. I also built a quick prototype of an "
                    "improved error handling library that reduced debugging time by 50%.\n\n"
                    "Result: Product leadership approved the 20% allocation. Over two quarters, incidents decreased "
                    "by 65%. Customer satisfaction scores improved by 15 points. The reliability allocation model "
                    "was adopted company-wide."
                ),
                "job_context": "Senior Engineer: influence, data-driven decision making, stakeholder management",
                "expected_score": 9,
            },
        ]

        leadership_bad = [
            {
                "question": "How do you handle underperforming team members?",
                "answer": "I would tell them they need to work harder. If they cannot improve, I would suggest they find a different job. Performance is important.",
                "job_context": "Engineering Manager: people management, performance improvement, mentoring",
                "expected_score": 2,
            },
            {
                "question": "Describe how you have driven technical strategy.",
                "answer": "I follow whatever the CTO tells me to do. I do not really have a role in driving technical strategy. I implement what I am told to implement.",
                "job_context": "Staff Engineer: technical strategy, architecture governance, organizational leadership",
                "expected_score": 2,
            },
            {
                "question": "How do you prioritize competing technical priorities?",
                "answer": "I just work on whatever is most urgent. I do not have a specific prioritization method. I try to get everything done as fast as possible.",
                "job_context": "Tech Lead: prioritization, stakeholder management, resource allocation",
                "expected_score": 3,
            },
            {
                "question": "Tell me about a time you influenced without authority.",
                "answer": "I usually just do what I am told. I do not really try to influence others because it is not my place. I focus on my own work.",
                "job_context": "Senior Engineer: influence, data-driven decision making, stakeholder management",
                "expected_score": 2,
            },
        ]
        for item in leadership_good + leadership_bad:
            tc.append({"id": idx, "category": "leadership", **item})
            idx += 1

        communication_good = [
            {
                "question": "How do you explain complex technical concepts to non-technical stakeholders?",
                "answer": (
                    "Situation: I needed to explain to our board of directors why we needed to invest $500K in "
                    "migrating from a legacy system that appeared to be working fine.\n\n"
                    "Task: Make the technical risks and business case clear to an audience with no engineering background.\n\n"
                    "Action: I avoided all technical jargon. I used the analogy of a building with a crumbling "
                    "foundation: it looks fine from outside, but the cracks are appearing. I showed concrete examples: "
                    "a 3-hour outage that cost $50K in lost revenue, a feature that took 3 months instead of 3 weeks "
                    "because of the legacy system. I presented a visual roadmap showing the migration in business terms: "
                    "new capabilities unlocked, revenue impact, and risk reduction.\n\n"
                    "Result: The board unanimously approved the $500K investment. They specifically praised the clarity "
                    "of the presentation. The migration was completed on budget and enabled two new product lines "
                    "generating $2M in annual revenue."
                ),
                "job_context": "CTO: executive communication, business alignment, technical advocacy",
                "expected_score": 9,
            },
            {
                "question": "Describe how you handle disagreements in technical design reviews.",
                "answer": (
                    "Situation: During a design review for our new payment processing system, two senior engineers "
                    "had fundamentally different approaches: event-sourced architecture vs traditional CRUD. The "
                    "discussion had been going in circles for two meetings.\n\n"
                    "Task: Facilitate a resolution while ensuring the best technical outcome.\n\n"
                    "Action: I paused the debate and asked each person to write a one-page proposal with explicit "
                    "assumptions, trade-offs, and rollback plans. I set up objective evaluation criteria: latency, "
                    "complexity, operational overhead, and team familiarity. I invited a neutral senior engineer from "
                    "another team to review both proposals. We scored each option against the criteria in a "
                    "spreadsheet together.\n\n"
                    "Result: The data-driven comparison made the trade-offs clear. We chose the event-sourced approach "
                    "for the high-throughput path and CRUD for admin operations. Both engineers felt the process was "
                    "fair. The decision was documented in our architecture decision records for future reference."
                ),
                "job_context": "Staff Engineer: design facilitation, technical decision making, documentation",
                "expected_score": 9,
            },
            {
                "question": "How do you communicate project status and risks to leadership?",
                "answer": (
                    "Situation: I was leading a critical platform migration with 8 engineers and a hard deadline "
                    "of Q4. At the midpoint, I identified two risks that could cause a 3-week delay.\n\n"
                    "Task: Communicate the risks transparently while proposing solutions and maintaining leadership "
                    "confidence in the project.\n\n"
                    "Action: I created a concise one-page status report with a traffic light system: green for on-track "
                    "items, amber for items with mitigation plans, red for items needing leadership decisions. For "
                    "each risk, I provided: current impact, probability, mitigation options with trade-offs, and my "
                    "recommendation. I presented this in a 15-minute meeting with the option to deep-dive on any area. "
                    "I also sent it 24 hours before the meeting so leaders could review in advance.\n\n"
                    "Result: Leadership appreciated the transparency and proactive communication. They approved one "
                    "mitigation (adding 2 contractors) and accepted the other risk with adjusted expectations. "
                    "The project was completed 1 week late instead of the feared 3-week delay. The status report "
                    "format was adopted as the standard for all engineering projects."
                ),
                "job_context": "Program Manager: project communication, risk management, executive reporting",
                "expected_score": 9,
            },
            {
                "question": "How would you handle delivering bad news about a missed deadline to a client?",
                "answer": (
                    "Situation: A key deliverable for our biggest client was going to be 2 weeks late due to an "
                    "unforeseen integration issue with their legacy system.\n\n"
                    "Task: Communicate the delay to the client while preserving the relationship and maintaining "
                    "trust.\n\n"
                    "Action: I called the client's project manager directly rather than sending an email. I was "
                    "honest about the cause without making excuses. I presented a revised timeline with specific "
                    "milestones, explained what we were doing to prevent similar issues, and offered a discount "
                    "on the next phase as goodwill. I also set up weekly check-ins until delivery was complete.\n\n"
                    "Result: The client appreciated the direct communication and transparency. They accepted the "
                    "revised timeline and the relationship actually strengthened. They expanded our contract by "
                    "30% the following quarter, citing our professional handling of the situation as a differentiator."
                ),
                "job_context": "Account Lead: client communication, relationship management, transparency",
                "expected_score": 9,
            },
            {
                "question": "Describe your approach to writing effective technical documentation.",
                "answer": (
                    "Situation: Our team's onboarding documentation was outdated and incomplete, causing new hires "
                    "to take 6 weeks instead of the planned 3 weeks to become productive.\n\n"
                    "Task: Overhaul the technical documentation to be accurate, accessible, and maintainable.\n\n"
                    "Action: I interviewed 5 recently onboarded engineers about what was missing or confusing. I "
                    "restructured docs into three levels: quickstart (30-minute setup), conceptual overview "
                    "(architecture and key decisions), and reference (API docs and runbooks). I added code examples "
                    "that were tested in CI to prevent drift. I created a documentation review step in our PR "
                    "process and assigned doc owners for each section.\n\n"
                    "Result: New engineer onboarding time dropped from 6 weeks to 2.5 weeks. The docs won an "
                    "internal engineering excellence award. Documentation maintenance became effortless because "
                    "of the CI-tested examples and PR review step."
                ),
                "job_context": "Senior Engineer: technical writing, documentation, developer experience",
                "expected_score": 9,
            },
        ]

        communication_bad = [
            {
                "question": "How do you explain technical concepts to non-technical people?",
                "answer": "I just tell them the technical details. If they do not understand, that is not my problem. They should learn some technical basics.",
                "job_context": "CTO: executive communication, business alignment, technical advocacy",
                "expected_score": 2,
            },
            {
                "question": "How do you handle disagreements in design reviews?",
                "answer": "I usually just go with whoever argues the loudest. I do not like confrontation so I avoid getting involved in disagreements. I just implement whatever is decided.",
                "job_context": "Staff Engineer: design facilitation, technical decision making, documentation",
                "expected_score": 2,
            },
            {
                "question": "How do you communicate project status to leadership?",
                "answer": "I send an email when the project is done. I do not think regular status updates are necessary unless there is a problem. I prefer to keep people out of my way so I can focus.",
                "job_context": "Program Manager: project communication, risk management, executive reporting",
                "expected_score": 2,
            },
            {
                "question": "How would you handle delivering bad news about a missed deadline?",
                "answer": "I would wait until the last minute to tell them. Maybe they will not notice. If they ask, I would blame the technical challenges and say it was out of my control.",
                "job_context": "Account Lead: client communication, relationship management, transparency",
                "expected_score": 2,
            },
            {
                "question": "Describe your approach to writing technical documentation.",
                "answer": "I do not write much documentation. I think code should be self-documenting. If someone does not understand the code, they should ask me. Documentation is a waste of time.",
                "job_context": "Senior Engineer: technical writing, documentation, developer experience",
                "expected_score": 2,
            },
        ]
        for item in communication_good + communication_bad:
            tc.append({"id": idx, "category": "communication", **item})
            idx += 1

        return tc

    def heuristic_score(self, answer: str, expected_score: int) -> int:
        score = 5

        length = len(answer)
        if length < 100:
            score -= 3
        elif length < 300:
            score -= 1
        elif length > 1000:
            score += 1
        elif length > 2000:
            score += 2

        lower = answer.lower()
        star_markers = ["situation:", "task:", "action:", "result:"]
        star_count = sum(1 for m in star_markers if m in lower)
        if star_count >= 4:
            score += 2
        elif star_count >= 2:
            score += 1
        elif star_count == 0:
            score -= 1

        has_numbers = bool(re.search(r"\b\d+(\.\d+)?%?\b", answer))
        if has_numbers:
            score += 1

        has_bullet = bool(re.search(r"[-•*]\s|^\s*\d+\.", answer, re.MULTILINE))
        if has_bullet:
            score += 1

        has_transition = any(
            phrase in lower
            for phrase in ["as a result", "because of", "this led to", "consequently", "therefore"]
        )
        if has_transition:
            score += 1

        words = answer.split()
        unique_words = set(w.lower() for w in words)
        if len(words) > 0 and len(unique_words) / len(words) > 0.6:
            score += 1

        vague = ["stuff", "things", "kind of", "sort of", "maybe", "i think", "i guess"]
        vague_count = sum(1 for v in vague if v in lower)
        if vague_count >= 2:
            score -= 1

        score = max(1, min(10, score))
        return score

    def run_harness(
        self,
        grader: Optional[STARGrader] = None,
        llm_service=None,
    ) -> Dict[str, Any]:
        test_data = self.load_test_data()
        results = []
        absolute_errors = []
        correct_within_1 = 0

        for case in test_data:
            if grader and llm_service:
                try:
                    grading = grader.grade_answer(
                        case["question"],
                        case["answer"],
                        case["job_context"],
                        llm_service,
                    )
                    predicted = grading["overall_score"]
                except Exception:
                    predicted = self.heuristic_score(case["answer"], case["expected_score"])
            else:
                predicted = self.heuristic_score(case["answer"], case["expected_score"])

            error = abs(predicted - case["expected_score"])
            absolute_errors.append(error)
            within_1 = error <= 1
            if within_1:
                correct_within_1 += 1

            results.append(
                {
                    "id": case["id"],
                    "category": case["category"],
                    "expected": case["expected_score"],
                    "predicted": predicted,
                    "error": error,
                    "within_1": within_1,
                }
            )

        mae = sum(absolute_errors) / len(absolute_errors) if absolute_errors else 0.0
        accuracy_within_1 = correct_within_1 / len(results) if results else 0.0

        category_summary: Dict[str, Dict[str, Any]] = {}
        for r in results:
            cat = r["category"]
            if cat not in category_summary:
                category_summary[cat] = {"count": 0, "total_error": 0, "within_1": 0}
            category_summary[cat]["count"] += 1
            category_summary[cat]["total_error"] += r["error"]
            if r["within_1"]:
                category_summary[cat]["within_1"] += 1

        for cat, data in category_summary.items():
            data["mae"] = data["total_error"] / data["count"] if data["count"] else 0.0
            data["accuracy_within_1"] = data["within_1"] / data["count"] if data["count"] else 0.0

        return {
            "mae": mae,
            "accuracy_within_1": accuracy_within_1,
            "results": results,
            "summary": {
                "total_cases": len(results),
                "category_breakdown": category_summary,
            },
        }
