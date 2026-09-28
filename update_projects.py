import os
import re
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
USERNAME = "ndree97"

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"

def fetch_repositories(username):
    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def generate_markdown(repos):
    project_lines = []
    # Exclude profile repository and any forks or private repos
    count = 0
    for repo in repos:
        if count >= 5:
            break
        if repo["fork"] or repo["private"] or repo["archived"]:
            continue
        if repo["name"].lower() == USERNAME.lower():
            continue
            
        name = repo["name"]
        desc = repo["description"] or "No description provided."
        stars = repo["stargazers_count"]
        url_repo = repo["html_url"]
        lang = repo["language"] or "Python"
        
        # Add badge or emoji based on main language
        lang_emoji = "🐍" if lang == "Python" else "⚙️" if lang == "C++" else "📦"
        
        line = f"- {lang_emoji} [**{name}**]({url_repo}) - *{lang}*  \n  {desc} (⭐ {stars})\n"
        project_lines.append(line)
        count += 1
        
    return "\n".join(project_lines)

try:
    repos = fetch_repositories(USERNAME)
    projects_content = generate_markdown(repos)
    
    readme_path = "README.md"
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()
        
    # Replace content between comments
    pattern = r"(<!-- START_SECTION:projects -->)(.*?)(<!-- END_SECTION:projects -->)"
    replacement = f"\\1\n\n{projects_content}\n\n\\3"
    updated_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_readme)
    print("README.md successfully updated with latest projects.")
except Exception as e:
    print(f"Error updating README.md: {e}")
