import os
import logging
import json
from typing import Optional, Dict, Any, List
from openai import OpenAI

logger = logging.getLogger(__name__)

class CodeFixer:
    def __init__(self):
        """Initialize the OpenAI-powered code fixer"""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Note: the newest OpenAI model is "gpt-4o" which was released May 13, 2024
        self.model = "gpt-4o"

    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze code for potential issues and improvements"""
        try:
            prompt = f"""Analyze this Python code for potential issues and provide suggestions:

            Code:
            {code}

            Provide analysis in JSON format with:
            - potential_issues: List of potential problems
            - suggestions: List of improvements
            - best_practices: List of best practice recommendations
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Python code analysis expert. Provide suggestions in Italian."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Error in code analysis: {str(e)}", exc_info=True)
            return {
                "potential_issues": ["Errore nell'analisi del codice"],
                "suggestions": [],
                "best_practices": []
            }

    def generate_tooltip(self, line: str, error_info: Dict) -> str:
        """Generate a tooltip message for the given line and error"""
        try:
            prompt = f"""Generate a helpful tooltip message in Italian for this code error:

            Line: {line}
            Error: {error_info.get('error_context', '')}
            Code: {error_info.get('code_snippet', '')}

            The tooltip should be concise and include:
            1. What's wrong
            2. How to fix it
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful code assistant. Provide concise tooltips in Italian."},
                    {"role": "user", "content": prompt}
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating tooltip: {str(e)}", exc_info=True)
            return "Errore nella generazione del suggerimento"

    def get_fix_suggestion(self, code: str, error_message: str) -> tuple[str, List[str]]:
        """Get fix suggestions for the code"""
        try:
            prompt = f"""Fix this Python code that produced the following error:

            Error:
            {error_message}

            Code:
            {code}

            Provide:
            1. The fixed code
            2. A list of explanations in Italian for what was fixed
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Python expert. Provide fixes and explanations in Italian."},
                    {"role": "user", "content": prompt}
                ]
            )

            fixed_code = response.choices[0].message.content
            explanations = ["Correzione applicata", "Codice aggiornato"]
            return fixed_code, explanations

        except Exception as e:
            logger.error(f"Error getting fix suggestion: {str(e)}", exc_info=True)
            return code, ["Errore nella generazione delle correzioni"]