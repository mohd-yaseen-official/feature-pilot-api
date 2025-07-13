import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from github import Github, GithubException
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate


class FeedbackToFeatureAgent:
    def __init__(self):
        # Validate environment variables
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPO")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_api_base = os.getenv("OPENAI_API_BASE")
        
        if not all([self.github_token, self.github_repo, self.openai_api_key]):
            raise ValueError("Missing required environment variables: GITHUB_TOKEN, GITHUB_REPO, OPENAI_API_KEY")
        
        # Set up OpenAI configuration
        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        if self.openai_api_base:
            os.environ["OPENAI_API_BASE"] = self.openai_api_base

        # Initialize GitHub client
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.github_repo)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-exp:free",
            temperature=0.1
        )
        
        # Create tools
        self.tools = [
            Tool.from_function(
                self.read_github_file,
                name="read_github_file",
                description="Reads a file from the GitHub repository and returns its contents."
            ),
            Tool.from_function(
                self.list_repo_files,
                name="list_repo_files",
                description="Lists files and directories in the specified path of the repository."
            ),
            Tool.from_function(
                self.analyze_file_structure,
                name="analyze_file_structure",
                description="Analyzes the structure of files in the repository to understand the project layout."
            ),
        ]
        
        # Create agent
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, prompt=self.prompt_template)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def _get_system_prompt(self) -> str:
        return """You are an expert AI developer assistant specialized in analyzing user feedback and implementing code changes to improve websites and applications.

    You have access to tools:
    1. Use list_repo_files() to explore the repository.
    2. Use read_github_file() to inspect actual file content.
    3. ONLY propose changes after reading and understanding the real code.

    Your capabilities:
    - Understand user feedback and translate it into code.
    - Work with HTML, React, or Next.js projects — detect and adapt accordingly.
    - Suggest precise, maintainable, and minimal code changes that follow project structure and style.

    REAL-WORLD FEEDBACK:
    - Users may submit incomplete, vague, or non-technical feedback.
    - Your job is to interpret user intent clearly even when the input lacks technical terms.
    - Always infer what the user meant based on common UX/UI/web dev patterns.
    - Never wait for perfect wording — act like a smart product developer who \"gets it\".

    When analyzing:
    - ALWAYS start by exploring the repo with list_repo_files()
    - Use read_github_file() to view actual implementation
    - NEVER assume structure — read and match it
    - Consider both immediate fixes and long-term improvements

    When proposing changes:
    - Modify existing code when possible — only add new code when necessary
    - Use the same format, indentation, naming, and structure already present
    - Be specific: file path, line number, current code (if applicable), and new code
    - Avoid breaking layout, logic, or framework conventions
    - Propose changes that improve usability, maintainability, or user experience
    - React/JSX: use proper camelCase props and component conventions
    - HTML: keep structure semantic and standards-compliant
    - Next.js: respect file-based routing and app/page structure

    CRITICAL: Return ONLY valid JSON in this exact format:
    {{
    \"feedback_analysis\": \"Brief summary of the feedback\",
    \"files_to_examine\": [\"list\", \"of\", \"relevant\", \"files\"],
    \"proposed_changes\": [
        {{
        \"file_path\": \"path/to/file\",
        \"change_type\": \"add|modify|delete\",
        \"line_number\": 123,
        \"current_code\": \"existing code (if applicable)\",
        \"new_code\": \"new code to insert or replace (single line only)\",
        \"reason\": \"why this change is needed\",
        \"impact\": \"what this improves or enables\"
        }}
    ],
    \"additional_recommendations\": \"any extra suggestions if relevant\"
    }}

    DO NOT include explanations, comments, JavaScript template literals, or invalid syntax.
    Only return valid JSON.

    SMART STRUCTURE RULES:
    - Before adding any new element, always check if a similar element (e.g. <h1>, nav, button) already exists. If so, update it instead of duplicating.
    - Never place visible content like headings, buttons, or links inside <head>. These belong in <body> or component layout regions.
    - If the user asks to "change the title" or "heading", update the visible page title (e.g. <h1>), not the <title> tag, unless explicitly stated.
    - When working with React or JSX files, follow component structure: use JSX syntax, preserve props, and respect functional/JSX return layout.
    - Always match the file type: HTML for plain .html files, JSX for React components, and Next.js conventions for app/pages folders.
    - Apply new changes in a way that fits naturally into the existing structure, classes, styles, and layout flow — don't break or override it.

    STRUCTURE RULES (Follow existing patterns, do not blindly rewrite):
    - Place layout elements like <nav>, <header>, <footer> inside the correct section (usually <body> or components), not in <head>
    - If navigation exists (e.g., <ul><li> or React components), reuse or modify — don't insert a redundant <nav>
    - Respect separation of concerns:
    - HTML: content and structure
    - CSS: styling in <style> or .css
    - JS: logic in <script> or .js
    - JSX: used only in .jsx/.tsx files
    - Follow the framework's conventions; detect if the code is React, Next.js, or static HTML, and act accordingly
    """

    def read_github_file(self, path: str) -> str:
        """Reads a file from the GitHub repository and returns its contents."""
        try:
            file = self.repo.get_contents(path, ref="main")
            content = file.decoded_content.decode('utf-8')
            return f"File: {path}\nContent:\n{content}"
        except GithubException as e:
            return f"Error reading {path}: {str(e)}"
        except Exception as e:
            return f"Unexpected error reading {path}: {str(e)}"

    def list_repo_files(self, path: str = "") -> str:
        """Lists files and directories in the specified path of the repository."""
        try:
            contents = self.repo.get_contents(path, ref="main")
            file_list = []
            for item in contents:
                file_list.append(f"{'📁' if item.type == 'dir' else '📄'} {item.path}")
            return f"Files in {path or 'root'}:\n" + "\n".join(file_list)
        except GithubException as e:
            return f"Error listing files in {path}: {str(e)}"

    def analyze_file_structure(self, path: str = "") -> str:
        """Analyzes the structure of files in the repository to understand the project layout."""
        try:
            contents = self.repo.get_contents(path, ref="main")
            structure = {"directories": [], "files": []}
            
            for item in contents:
                if item.type == 'dir':
                    structure["directories"].append(item.path)
                else:
                    structure["files"].append(item.path)
            
            return f"Repository structure analysis for {path or 'root'}:\n" + json.dumps(structure, indent=2)
        except GithubException as e:
            return f"Error analyzing structure in {path}: {str(e)}"

    def analyze_feedback(self, feedback: str) -> Dict[str, Any]:
        """Analyzes user feedback and proposes code changes."""
        # Get the actual list of files in the repo
        file_list = self.list_all_files()
        file_list_str = '\n'.join(file_list)
        prompt = f"""
        You are analyzing this user feedback:

        \"{feedback}\"

        Your task:
        1. Use list_repo_files() to explore the project structure.
        2. Use read_github_file() to read actual file content.
        3. THEN and ONLY THEN propose changes based on the real code.

        The project may be plain HTML, React, or Next.js. Detect the framework and adapt your changes accordingly.

        Files available:
        {file_list_str}

        Return a JSON object in this EXACT format (no line breaks inside values):

        {{{{ 
        \"feedback_analysis\": \"brief summary of the feedback\",
        \"files_to_examine\": [\"list\", \"of\", \"files\", \"you\", \"read\"],
        \"proposed_changes\": [
            {{{{ 
            \"file_path\": \"path/to/file\",
            \"change_type\": \"add|modify|delete\",
            \"line_number\": 123,
            \"current_code\": \"existing code (if applicable)\",
            \"new_code\": \"replacement code (must be one line)\",
            \"reason\": \"why this change is needed\",
            \"impact\": \"what this change improves or enables\"
            }}}}
        ],
        \"additional_recommendations\": \"any other good suggestions\"
        }}}}

        🧠 THINK LIKE A REAL DEVELOPER:

        - Use existing structure: DO NOT insert new <nav>, <div>, <section>, or <style> if the purpose is already handled with <ul>, <header>, or classed containers.
        - Respect framework conventions:
        - ✅ HTML: use <head>, <body>, and semantic tags properly.
        - ✅ React: use JSX, self-closing tags, camelCase props, no <script>.
        - ✅ Next.js: use app/pages structure, component-based layout.
        - Do not inject layout elements (like <nav>, <footer>) inside <head>.
        - NEVER suggest code that violates HTML/JS/CSS boundaries.
        - Only suggest small, precise edits — modify what's already there unless absolutely necessary to create new.
        - Don't duplicate functionality (e.g., avoid adding \"Login\" buttons if one exists already — improve or style it).
        - If the file uses a consistent structure (e.g., ul>li for nav), maintain it — DO NOT refactor to <nav> without reason.
        - Always match indentation, naming patterns, and style already used.
        - Avoid inline styles unless the rest of the file uses them.

        DO NOT explain anything. DO NOT include JavaScript, template literals, or multiline strings inside values. Return only valid JSON.
        Remember: Use the tools first, then return only valid JSON!
        """
        try:
            result = self.executor.invoke({"input": prompt})
            # Try to extract JSON from the response
            response_text = result.get("output", "")
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    # Clean up the JSON string to fix common issues
                    json_str = json_match.group()
                    # Remove newlines and extra spaces in string values
                    json_str = re.sub(r'\n\s*', ' ', json_str)
                    # Fix unescaped quotes in strings
                    json_str = re.sub(r'(?<!\\)"', '"', json_str)
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    # If still fails, try to extract just the structure
                    return {
                        "error": f"JSON parsing failed: {str(e)}",
                        "raw_response": response_text,
                        "attempted_cleanup": True
                    }
            else:
                return {
                    "error": "Could not parse JSON response",
                    "raw_response": response_text
                }
        except Exception as e:
            return {
                "error": f"Error analyzing feedback: {str(e)}",
                "feedback": feedback
            }

    def validate_proposal(self, proposal: Dict[str, Any]) -> bool:
        """Validates a proposed change."""
        if "error" in proposal:
            return False
        
        required_fields = ["feedback_analysis", "proposed_changes"]
        if not all(field in proposal for field in required_fields):
            return False
        
        for change in proposal.get("proposed_changes", []):
            required_change_fields = ["file_path", "change_type", "new_code", "reason"]
            if not all(field in change for field in required_change_fields):
                return False
        
        return True

    def list_all_files(self, path="") -> list:
        """Recursively list all files in the repository starting from the given path."""
        all_files = []
        try:
            contents = self.repo.get_contents(path, ref="main")
            for item in contents:
                if item.type == "dir":
                    all_files.extend(self.list_all_files(item.path))
                elif item.type == "file":
                    all_files.append(item.path)
        except GithubException as e:
            pass  # Ignore folders that can't be accessed
        return all_files

    def find_file_with_code(self, code_snippet: str) -> Optional[str]:
        """Find the file in the repo that contains the given code snippet."""
        all_files = self.list_all_files()
        for file_path in all_files:
            try:
                file = self.repo.get_contents(file_path, ref="main")
                content = file.decoded_content.decode('utf-8')
                if code_snippet and code_snippet in content:
                    return file_path
            except Exception:
                continue
        return None

    def apply_changes(self, proposal: Dict[str, Any]) -> List[str]:
        """Applies the proposed changes to the repository."""
        results = []
        
        for change in proposal.get("proposed_changes", []):
            try:
                file_path = change["file_path"]
                change_type = change["change_type"]
                new_code = change["new_code"]
                reason = change["reason"]
                current_code = change.get("current_code", "")

                # Try to find the correct file if current_code is specified and file_path is missing or 404
                found_file = None
                if current_code:
                    found_file = self.find_file_with_code(current_code)
                if found_file:
                    file_path = found_file

                # Get current file content
                try:
                    file = self.repo.get_contents(file_path, ref="main")
                    current_content = file.decoded_content.decode('utf-8')
                except GithubException as e:
                    if e.status == 404 and change_type == "add":
                        current_content = ""
                        file = None
                    else:
                        results.append(f"❌ File {file_path} not found for {change_type} operation.")
                        continue

                # Apply changes based on type
                if change_type == "add":
                    if change.get("line_number") is not None:
                        lines = current_content.splitlines()
                        lines.insert(change["line_number"] - 1, new_code)
                        new_content = "\n".join(lines)
                    else:
                        new_content = current_content + "\n" + new_code
                elif change_type == "modify":
                    if change.get("line_number") is not None:
                        lines = current_content.splitlines()
                        lines[change["line_number"] - 1] = new_code
                        new_content = "\n".join(lines)
                    else:
                        new_content = current_content.replace(current_code, new_code)
                elif change_type == "delete":
                    if change.get("line_number") is not None:
                        lines = current_content.splitlines()
                        del lines[change["line_number"] - 1]
                        new_content = "\n".join(lines)
                    else:
                        new_content = current_content.replace(current_code, "")
                else:
                    results.append(f"❌ Unknown change type: {change_type}")
                    continue

                # Create branch
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                branch_name = f"ai-feedback-{timestamp}-{hash(file_path) % 10000}"

                # Create branch from main
                main_branch = self.repo.get_branch("main")
                self.repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)

                # Commit changes
                if file is None and change_type == "add":
                    self.repo.create_file(
                        path=file_path,
                        message=f"AI Feedback Implementation: {reason}",
                        content=new_content,
                        branch=branch_name
                    )
                else:
                    self.repo.update_file(
                        path=file_path,
                        message=f"AI Feedback Implementation: {reason}",
                        content=new_content,
                        sha=file.sha,
                        branch=branch_name
                    )

                # Create pull request
                pr = self.repo.create_pull(
                    title=f"AI Feedback: {reason}",
                    body=f"""
## AI-Generated Changes

**Feedback Analysis:** {proposal.get('feedback_analysis', 'N/A')}

**Change Details:**
- **File:** {file_path}
- **Type:** {change_type}
- **Reason:** {reason}

**Impact:** {change.get('impact', 'N/A')}

This change was automatically generated based on user feedback analysis.
Please review the changes and test thoroughly before merging.
                    """.strip(),
                    head=branch_name,
                    base="main"
                )
                results.append(f"✅ PR Created: {pr.html_url}")
            except Exception as e:
                results.append(f"❌ Error applying change to {file_path}: {str(e)}")
        return results 