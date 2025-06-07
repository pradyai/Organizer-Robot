Recommended Settings:
    Branch name pattern: main
    Require a pull request before merging: ✓
    Require approvals: 2 (for 4-person team)
    Dismiss stale PR approvals when new commits are pushed: ✓
    Require status checks to pass before merging: ✓
    Require branches to be up to date before merging: ✓
    Include administrators: ✓


Getting Started (for each team member):
# Clone the repository
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Build and run development environment
cd docker
docker-compose up -d dev

# Enter the container
docker-compose exec dev bash

# Run tests
pytest

# Start Jupyter (optional)
docker-compose up jupyter
# Access at http://localhost:8888

Daily Workflow:
Create feature branch: git checkout -b feature/your-feature
Develop in container: docker-compose exec dev bash
Run tests: pytest
Format code: black src tests && isort src tests
Commit changes: git add . && git commit -m "feat: description"
Push and create PR: git push origin feature/your-feature
Wait for 2 approvals before merging