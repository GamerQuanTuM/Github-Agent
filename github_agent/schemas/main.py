from pydantic import Field, BaseModel
from typing import Optional, List


class IssueReaderAgentOutput(BaseModel):
    title: str = Field(..., description="Title of the issue.")
    body: str = Field(..., description="Description of the issue.")
    issue_number: str = Field(..., description="Issue number.")
    referenced_files: Optional[List[str]] = Field(
        None, description="Files referenced in the issue.")
    error_messages: Optional[List[str]] = Field(
        None, description="Error messages associated with the issue.")
    problem_summary: Optional[str] = Field(None, description="Summary of the issue.")


class RepoNavigatorAgentOutput(BaseModel):
    target_file: str = Field(..., description="Relative path to the file most likely responsible for the issue.")
    target_function: str = Field(..., description="The specific function, method, or class where the issue occurs.")
    reasoning: str = Field(..., description="Short explanation describing why this file/function is responsible.")
    code_snippet: str = Field(..., description="The minimal extracted code snippet relevant to the issue.")
    full_file: str = Field(..., description="The entire file content.")

class CodeFixAgentOutput(BaseModel):
    updated_file: str = Field(..., description="The updated file content with the fix applied.")
    code_fix_summary: str = Field(..., description="A brief summary of the changes made.")

