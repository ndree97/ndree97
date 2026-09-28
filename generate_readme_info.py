import os
import re
import time
import requests

USERNAME = "ndree97"
TOKEN = os.getenv("GH_TOKEN") or os.getenv("METRICS_TOKEN") or os.getenv("GITHUB_TOKEN")

headers = {
    "Accept": "application/vnd.github.v3+json",
}
if TOKEN:
    headers["Authorization"] = f"token {TOKEN}"

def get_contributed_repos(username):
    repos = []
    if TOKEN:
        query = f"""
        query {{
          user(login: "{username}") {{
            repositoriesContributedTo(last: 100, includeUserRepositories: true) {{
              nodes {{
                isFork
                name
                owner {{
                  login
                }}
              }}
            }}
          }}
        }}
        """
        try:
            res = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)
            if res.status_code == 200:
                nodes = res.json().get("data", {}).get("user", {}).get("repositoriesContributedTo", {}).get("nodes", [])
                for node in nodes:
                    if not node.get("isFork"):
                        repos.append({"owner": node["owner"]["login"], "name": node["name"]})
        except Exception as e:
            print(f"GraphQL query error: {e}")

    try:
        res = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100", headers=headers)
        if res.status_code == 200:
            for r in res.json():
                if not r.get("fork"):
                    item = {"owner": r["owner"]["login"], "name": r["name"]}
                    if item not in repos:
                        repos.append(item)
    except Exception as e:
        print(f"REST repos query error: {e}")

    return repos

def format_intword(n):
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f} billion"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.1f} million"
    elif n >= 1_000:
        return f"{n / 1_000:.1f} thousand"
    return str(n)

def get_lines_of_code(repos):
    print("Calculating Lines Of Code...")
    total_loc = 0
    for repo in repos:
        owner = repo["owner"]
        name = repo["name"]
        url = f"https://api.github.com/repos/{owner}/{name}/stats/code_frequency"
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 202:
                time.sleep(1.5)
                r = requests.get(url, headers=headers)
            if r.status_code == 200 and isinstance(r.json(), list):
                for week in r.json():
                    additions = week[1]
                    deletions = abs(week[2])
                    total_loc += max(0, additions - deletions)
        except Exception as e:
            print(f"Error fetching code frequency for {owner}/{name}: {e}")

    formatted_loc = format_intword(int(total_loc)) if total_loc > 0 else "thousands of"
    return f"**From Hello World I have written {formatted_loc} Lines of Code 🧑‍💻**"

def get_profile_views(username):
    print("Fetching Profile Views...")
    url = f"https://api.github.com/repos/{username}/{username}/traffic/views"
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            count = r.json().get("count", 0)
            return f"**✨ {count} people were here!**"
    except Exception as e:
        print(f"Error fetching traffic views: {e}")
    return "**✨ Welcome to my GitHub Profile!**"

def update_section(content, start_tag, end_tag, replacement_text):
    pattern = rf"({re.escape(start_tag)})([\s\S]*?)({re.escape(end_tag)})"
    return re.sub(pattern, lambda m: f"{m.group(1)}\n{replacement_text}\n{m.group(3)}", content)

def main():
    show_lines_of_code = os.getenv("SHOW_LINES_OF_CODE", "True").lower() == "true"
    show_profile_views = os.getenv("SHOW_PROFILE_VIEWS", "True").lower() == "true"

    readme_path = "README.md"
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()

    repos = get_contributed_repos(USERNAME)

    if show_profile_views:
        views_stat = get_profile_views(USERNAME)
        readme = update_section(
            readme,
            "<!--START_SECTION_PROFILE_VIEWS:readme-info-->",
            "<!--END_SECTION_PROFILE_VIEWS:readme-info-->",
            views_stat
        )

    if show_lines_of_code:
        loc_stat = get_lines_of_code(repos)
        readme = update_section(
            readme,
            "<!--START_SECTION_LINES_OF_CODE:readme-info-->",
            "<!--END_SECTION_LINES_OF_CODE:readme-info-->",
            loc_stat
        )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)
    print("README.md successfully updated with README Info stats.")

if __name__ == "__main__":
    main()
