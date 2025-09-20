# Chapter 1: The Future of Software Creation

- **Speaker:** Amjad Masad, CEO of Replit
- **Date:** 2025-09-12
- **Source:** [YouTube](https://www.youtube.com/watch?v=lWmDiDGsLK4)

## Introduction: From Expert Tools to Everyday Creation

If you look at the history of computing, mainframes were the first mainstream devices, and you needed to be an expert to use one. Then, PCs came along. Initially, they were dismissed as toys for things like MacPaint; there wasn't a serious business use case until the spreadsheet arrived. The spreadsheet was the first truly useful software for the average person, and now PCs—from desktops to the servers in data centers—run the world economy.

We see the same pattern in software engineering. The modern software career began in the 1970s with the rise of Unix and C. It required years of college education and several more years of on-the-job training to become proficient.

Today, software itself is undergoing the same transition: moving from a tool for experts to a medium for everyone. This is the core principle for which we are building Replit. Our vision has always been to make it so that anyone can write software. We built an IDE, language runtimes, a sandboxed cloud environment, and deployment services. When AI appeared, we realized the ultimate expression of our mission was to make it so you don't have to code at all. Code is the bottleneck.

## The Inevitable Rise of Software-Building Agents

In late 2023 and early 2024, we decided to put all our resources into agents. At the time, agents barely worked, but benchmarks like SWE-bench—a collection of real-world GitHub issues—showed a clear trend. In 2022, performance was near zero. In 2023, it started working. By early 2024, we were on a trajectory that signaled large parts of software engineering were on the verge of being automated. Today, we're achieving 70-80% on SWE-bench.

This doesn't mean we've automated all of software engineering, but we are well on our way to creating truly useful software engineering agents. This trend holds true for anyone building agent startups: believe that it's coming. I tell my team that we need to be comfortable building seemingly "crappy" products today, because in two months, the underlying models will improve and suddenly make the product viable.

## The "Habitat": Why Infrastructure is the Hard Part

Agents that can write code are the easy part. The hard part is the infrastructure around them—what I call the **habitat** in which the agent lives.

You need a virtual machine in the cloud, not on your local computer, because agents can be unpredictable and need to be sandboxed. This environment must be scalable to millions of users and support every language and package. Agents are trained in standard Linux environments; they need to use the shell, read and write files, and install both system-level and language-level packages. Many current agent environments are too constrained. You need an open environment that mirrors how a human software engineer works.

To ship real software, agents also need access to deployments, databases, authentication, secrets management, and background jobs. At Replit, we provide these as built-in services. For example, instead of asking an agent to build an authentication system (which they aren't very good at), a user can ask the Replit agent to integrate auth, and it will simply turn on our built-in, one-line-of-code service.

Our roadmap includes universal model access, so you can use any model without managing API keys, and payments. Payments are crucial not just for entrepreneurs to charge for their applications, but for the agents themselves. In the future, an agent should have its own wallet to pay for services, like a Twilio integration. A more radical idea is that an agent should be able to hire humans from a service like TaskRabbit to solve problems it can't, like a CAPTCHA.

## The Levels of Autonomy

We can think about agent progress in terms of levels of autonomy, similar to self-driving cars.

- **Level 1: Code Assistance.** This was the language server, providing basic IntelliSense.
- **Level 2: AI Code Completion.** This is GitHub Copilot.
- **Level 3: Partial Automation.** Our first Replit agent could work for 10-15 minutes on its own but required frequent human input to test and verify its work.
- **Level 4: Full Autonomy (with Supervision).** This is what we're building now with Agent V3. It works almost entirely on its own but still needs some supervision.
- **Level 5: Massively Scaled Autonomy.** In the next couple of years, we'll reach a point where you can spin up a thousand agents, give them a thousand problems, and be confident that 95% of them will succeed with very little supervision.

To achieve Level 4, our Agent V3 is built on three pillars:
1.  **End-to-End Testing with Computer Use:** We are at the frontier of "computer use," where models can interact with a GUI like a human. It's slow and expensive now, but in 3-6 months, it will improve dramatically and allow the agent to QA its own work.
2.  **Test-Time Compute and Simulations:** The best models get more intelligent the more tokens they process. We want the agent to not just "think" in text but to form hypotheses and test them in a real environment. We built a transactional, reversible file system that allows the agent to fork its environment, try multiple solutions to a problem in parallel, and merge the best one.
3.  **Automated Test Generation:** For every feature it builds, the agent must also generate tests to ensure it doesn't break existing functionality later. This is harder than it sounds, as models are not yet great at writing robust unit tests.

## The Future: Zero-Cost Software and the Sovereign Individual

My prediction is that all application software will go to zero. In other words, software will become so cheap to produce that no one will make money on traditional SaaS. If anyone can generate software of any complexity with a single prompt, its value will plummet.

Think of the vast ecosystem of generic and vertical SaaS tools that businesses buy today. Soon, you'll be able to replace most of them by writing your own with an agent. One of our colleagues in HR, who had never written a line of code, built a custom org chart software in three days because the expensive market solutions didn't fit her needs. That's happening today. Project that out a few years, and the software business is fundamentally disrupted.

This shift also changes how we work. The Industrial Revolution led to specialization. The modern economy is built on a factory assembly line model where each person is a specialist. But when your HR professional is also a software engineer, a marketer, and more—because they have AI agents to assist them—jobs become less specialized.

The company structure will start to look more like a network than a hierarchy, more like an open-source project than a traditional corporation. Every employee's mandate becomes: "Make the business work." Everyone becomes an entrepreneur.

This leads to the rise of what the book *The Sovereign Individual* called a person so empowered by technology that they can create enormous wealth individually. Satoshi, the anonymous creator of Bitcoin, generated over a trillion dollars of value as a single person. This will become a common occurrence. The most exciting part is that access to opportunity becomes universal. It doesn't matter if you're in Silicon Valley or anywhere else. If you can think clearly and generate good ideas, you can build.

Collaboration will also change. The "one-person billion-dollar company" misses the point. What's truly interesting is the ability to assemble and unwind teams of people and agents with incredible speed for specific missions. The transaction cost of finding and hiring a developer—human or AI—will drop to near zero, like ordering an Uber.

Ultimately, to survive, businesses like Replit must shift from making applications to solving problems directly with software.

---

## Q&A

**Audience Member:** In this future, will humans engage with a single, unilateral agent or multiple agents? How would we handle the fragmentation of data and context across them?

**Amjad Masad:** I believe it will be a multi-agent world. Someone with true, unique domain expertise—say, a top lawyer for rare cases—won't open-source their knowledge. Instead, they will imbue it into a specialized agent to scale themselves. There will be developer agents, specialized agents, and orchestrator agents that assemble teams of other agents. Just as you provide context when you hire a lawyer today, you will provide context to these agents. We will need new, more interesting protocols for agent-to-agent communication.

**Audience Member:** If AI can automate most physical and cognitive tasks, what is left for humans to do?

**Amjad Masad:** This depends on your worldview. My view is that there is something special about humans and that current AI has fundamental limitations. It cannot truly generalize out of distribution; everything it does must be represented in its training data. For a truly novel problem, you still need human ingenuity. Humans will move into the creative seat. Agents can be creative in a combinatorial way, but generating net-new knowledge and ideas will remain a human endeavor. The exciting part is that people can generate novel ideas and test them almost instantly.

**Audience Member:** You mentioned the value of clear thinking. Is this an argument for a liberal arts, critical-thinking model of education over a STEM-focused one?

**Amjad Masad:** I don't think they are mutually exclusive, but I do believe the liberal arts will become more valuable. In the future, everyone will need to be more of a generalist. Engineers today can afford to be parochial and not even understand the business they're in. In the future, people will need a broader worldview and skill set, but a scientific mindset will remain important.

**Audience Member:** Where in the tech stack is Replit making the progress that allows your agent to work autonomously for an hour?

**Amjad Masad:** It's in what I call the "habitat." The commercial model providers can train great models, but an agent company like ours must provide the infrastructure for that agent to exist in. The crucial piece for us is that our environment is transactional and atomic. Every change is a snapshot, so you can go back to any point in history and reboot the application in that state. We believe this infrastructure—giving the agent the ability to get feedback and try things rapidly—is the key to reaching the upper echelons of reliability, more so than training alone.

**Audience Member:** What roles today can set someone up to be a successful generalist in the future?

**Amjad Masad:** Join startups as early as possible. The earlier you join, the more generalist experience you get. But even if you join a slightly larger startup, you must actively seek generalist opportunities. Don't wait for tasks. Wake up with a mission: "My job is to make this company succeed."

**Audience Member:** How do you approach balancing the push for longer autonomous time horizons versus improving reasoning for shorter horizons?

**Amjad Masad:** We do both. Improving reliability for shorter horizons is about investing in reasoning and the parallel trial-and-error simulations I mentioned. Achieving longer horizons is about removing the human from the loop, which requires automated testing. As an agent works longer, it can experience "goal drift." Having the guardrails of tests keeps it coherent over time.

**Audience Member:** Should we be concerned about agents oversaturating certain sectors?

**Amjad Masad:** Certainly. The software engineering agent space is already very tricky. If you're coming in late, you need a truly novel idea. But many other areas are wide open. Who is building the agent for HR or finance? My advice is to start with what you are interested in and where you have domain knowledge. If you are a compliance officer, you are the best person to start a compliance agent company because domain knowledge is the most important asset.

**Audience Member:** If the cost of building software goes to zero, how will platforms like Replit make money and compete?

**Amjad Masad:** I said *application* software, not all software. Software will continue to run our lives, but much of it will be autonomous and personal. For example, I use Replit to build personal software to manage my life and quantified-self data. Instead of me doing that, I should be able to tell the Replit agent my goals, and it should figure out what software to build, what wearables to buy, and how to operate everything to solve my problem. Replit needs to become a universal problem solver to survive. Where Replit excels today is that it is full-stack—it can take you from an idea to a deployed and scaled piece of software.

**Audience Member:** In a future where code is written and tested by agents, how do we prevent the "model collapse" problem of accumulating errors from training on AI-generated data?

**Amjad Masad:** My bet is that we will soon move to a more AlphaZero-style of training. You start with a model trained on all of the internet's human-generated code. But the next generation will be trained in a reinforcement learning environment where it does self-play: generating problems, solving them, getting feedback, and iterating in a massively parallel way. It won't be trained on static human code. We have to solve this, or we will plateau very hard.

**Audience Member:** Is any of your work on the agent habitat, like the copy-on-write file system, publicly available or open source?

**Amjad Masad:** We have open-sourced some of our package manager work and are big contributors to NixOS, which is a transactional operating system generator. We will at minimum talk more about the file system work in the future. But this is all active work right now. You should come intern at Replit to learn this stuff and then go build it yourself.