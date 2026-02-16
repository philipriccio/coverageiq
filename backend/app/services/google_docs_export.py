"""Google Docs export service for coverage reports.

This module handles exporting CoverageIQ reports to Google Docs format,
including proper formatting, styling, and sharing.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Path to credentials file
CREDENTIALS_PATH = os.environ.get(
    "GOOGLE_CREDENTIALS_PATH",
    "/data/.openclaw/workspace/google-drive-credentials.json"
)

# Token file for OAuth
TOKEN_PATH = os.environ.get(
    "GOOGLE_TOKEN_PATH",
    "/data/.openclaw/workspace/.google-token.json"
)


class GoogleDocsExportError(Exception):
    """Raised when Google Docs export fails."""
    pass


class GoogleDocsExporter:
    """Export coverage reports to Google Docs.
    
    This class handles:
    - Creating Google Docs with proper formatting
    - Adding styled content (headers, bold text, etc.)
    - Sharing documents with specified users
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize the exporter.
        
        Args:
            credentials_path: Path to Google OAuth credentials JSON file
        """
        self.credentials_path = credentials_path or CREDENTIALS_PATH
        self.token_path = TOKEN_PATH
        self._service = None
        self._drive_service = None
    
    def _get_credentials(self) -> Credentials:
        """Get or refresh Google API credentials.
        
        Returns:
            Valid Credentials object
            
        Raises:
            GoogleDocsExportError: If credentials cannot be obtained
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(
                    self.token_path, 
                    ['https://www.googleapis.com/auth/documents',
                     'https://www.googleapis.com/auth/drive']
                )
            except Exception as e:
                print(f"Error loading token: {e}")
        
        # If credentials are valid, return them
        if creds and creds.valid:
            return creds
        
        # For service account or initial setup, load from credentials file
        try:
            with open(self.credentials_path, 'r') as f:
                creds_data = json.load(f)
            
            # Check if this is an installed app OAuth credential
            if 'installed' in creds_data:
                # For OAuth flow, we need to use the credentials
                from google_auth_oauthlib.flow import InstalledAppFlow
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    ['https://www.googleapis.com/auth/documents',
                     'https://www.googleapis.com/auth/drive']
                )
                
                # Run local server for auth
                creds = flow.run_local_server(port=0)
                
                # Save the token
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                
                return creds
            else:
                raise GoogleDocsExportError(
                    "Unsupported credential format. Expected OAuth installed app credentials."
                )
                
        except FileNotFoundError:
            raise GoogleDocsExportError(
                f"Credentials file not found: {self.credentials_path}"
            )
        except Exception as e:
            raise GoogleDocsExportError(f"Failed to get credentials: {str(e)}")
    
    @property
    def docs_service(self):
        """Lazy-load the Google Docs API service."""
        if self._service is None:
            creds = self._get_credentials()
            self._service = build('docs', 'v1', credentials=creds)
        return self._service
    
    @property
    def drive_service(self):
        """Lazy-load the Google Drive API service."""
        if self._drive_service is None:
            creds = self._get_credentials()
            self._drive_service = build('drive', 'v3', credentials=creds)
        return self._drive_service
    
    def create_document(self, title: str) -> str:
        """Create a new Google Doc.
        
        Args:
            title: Document title
            
        Returns:
            Document ID
            
        Raises:
            GoogleDocsExportError: If creation fails
        """
        try:
            document = self.docs_service.documents().create(body={
                'title': title
            }).execute()
            return document['documentId']
        except HttpError as e:
            raise GoogleDocsExportError(f"Failed to create document: {str(e)}")
    
    def share_document(self, doc_id: str, email: str, role: str = 'writer') -> None:
        """Share a document with a user.
        
        Args:
            doc_id: Google Doc ID
            email: Email address to share with
            role: Permission role ('reader', 'commenter', 'writer')
            
        Raises:
            GoogleDocsExportError: If sharing fails
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            self.drive_service.permissions().create(
                fileId=doc_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
        except HttpError as e:
            raise GoogleDocsExportError(f"Failed to share document: {str(e)}")
    
    def add_content(self, doc_id: str, content: List[Dict[str, Any]]) -> None:
        """Add formatted content to a document.
        
        Args:
            doc_id: Google Doc ID
            content: List of content items with text and style info
            
        Raises:
            GoogleDocsExportError: If adding content fails
        """
        try:
            requests = []
            current_index = 1  # Start after initial paragraph
            
            for item in content:
                text = item.get('text', '')
                style = item.get('style', 'NORMAL_TEXT')
                bold = item.get('bold', False)
                
                # Insert text
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': text + '\n'
                    }
                })
                
                # Apply style
                end_index = current_index + len(text) + 1
                
                if style == 'HEADING_1':
                    requests.append({
                        'updateParagraphStyle': {
                            'range': {
                                'startIndex': current_index,
                                'endIndex': end_index
                            },
                            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
                            'fields': 'namedStyleType'
                        }
                    })
                elif style == 'HEADING_2':
                    requests.append({
                        'updateParagraphStyle': {
                            'range': {
                                'startIndex': current_index,
                                'endIndex': end_index
                            },
                            'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                            'fields': 'namedStyleType'
                        }
                    })
                
                # Apply bold if needed
                if bold:
                    requests.append({
                        'updateTextStyle': {
                            'range': {
                                'startIndex': current_index,
                                'endIndex': end_index
                            },
                            'textStyle': {'bold': True},
                            'fields': 'bold'
                        }
                    })
                
                current_index = end_index
            
            # Execute batch update
            if requests:
                self.docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
                
        except HttpError as e:
            raise GoogleDocsExportError(f"Failed to add content: {str(e)}")
    
    def export_coverage_report(
        self,
        report_data: Dict[str, Any],
        share_with: Optional[str] = None
    ) -> Dict[str, str]:
        """Export a coverage report to Google Docs.
        
        This is the main method that creates a formatted coverage report
        in Google Docs with proper styling.
        
        Args:
            report_data: The coverage report data
            share_with: Optional email to share the document with
            
        Returns:
            Dict with 'document_id', 'url', and 'title'
            
        Raises:
            GoogleDocsExportError: If export fails
        """
        try:
            # Extract report info
            script_title = report_data.get('script_title', 'Untitled Script')
            timestamp = datetime.now().strftime("%Y-%m-%d")
            doc_title = f"Coverage Report: {script_title} - {timestamp}"
            
            # Create document
            doc_id = self.create_document(doc_title)
            
            # Build content
            content = self._format_report_content(report_data)
            
            # Add content to document
            self.add_content(doc_id, content)
            
            # Share if email provided
            if share_with:
                self.share_document(doc_id, share_with, role='writer')
            
            # Get document URL
            url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            return {
                'document_id': doc_id,
                'url': url,
                'title': doc_title
            }
            
        except Exception as e:
            raise GoogleDocsExportError(f"Export failed: {str(e)}")
    
    def _format_report_content(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format coverage report data into Google Docs content.
        
        Args:
            report_data: The coverage report data
            
        Returns:
            List of content items for Google Docs API
        """
        content = []
        
        # Header
        script_title = report_data.get('script_title', 'Untitled Script')
        content.append({
            'text': f'CoverageIQ Report: {script_title}',
            'style': 'HEADING_1',
            'bold': True
        })
        
        # Generation info
        timestamp = datetime.now().strftime("%B %d, %Y")
        content.append({
            'text': f'Generated on {timestamp}',
            'style': 'NORMAL_TEXT',
            'bold': False
        })
        content.append({'text': '', 'style': 'NORMAL_TEXT'})  # Empty line
        
        # Scores Section
        content.append({
            'text': 'SCORES & RECOMMENDATION',
            'style': 'HEADING_2',
            'bold': True
        })
        
        total_score = report_data.get('total_score', 0)
        recommendation = report_data.get('recommendation', 'N/A')
        content.append({
            'text': f'Total Score: {total_score}/50',
            'style': 'NORMAL_TEXT',
            'bold': True
        })
        content.append({
            'text': f'Recommendation: {recommendation}',
            'style': 'NORMAL_TEXT',
            'bold': True
        })
        
        # Subscores
        subscores = report_data.get('subscores', {})
        if subscores:
            content.append({'text': '', 'style': 'NORMAL_TEXT'})
            content.append({
                'text': 'Subscores:',
                'style': 'NORMAL_TEXT',
                'bold': True
            })
            for category, score_data in subscores.items():
                if isinstance(score_data, dict):
                    score = score_data.get('score', 0)
                    rationale = score_data.get('rationale', '')
                    content.append({
                        'text': f'  • {category.capitalize()}: {score}/10',
                        'style': 'NORMAL_TEXT',
                        'bold': False
                    })
                    if rationale:
                        content.append({
                            'text': f'    {rationale}',
                            'style': 'NORMAL_TEXT',
                            'bold': False
                        })
                else:
                    content.append({
                        'text': f'  • {category.capitalize()}: {score_data}/10',
                        'style': 'NORMAL_TEXT',
                        'bold': False
                    })
        
        content.append({'text': '', 'style': 'NORMAL_TEXT'})
        
        # Logline
        logline = report_data.get('logline', '')
        if logline:
            content.append({
                'text': 'LOGLINE',
                'style': 'HEADING_2',
                'bold': True
            })
            content.append({
                'text': logline,
                'style': 'NORMAL_TEXT',
                'bold': False
            })
            content.append({'text': '', 'style': 'NORMAL_TEXT'})
        
        # Synopsis
        synopsis = report_data.get('synopsis', '')
        if synopsis:
            content.append({
                'text': 'SYNOPSIS',
                'style': 'HEADING_2',
                'bold': True
            })
            content.append({
                'text': synopsis,
                'style': 'NORMAL_TEXT',
                'bold': False
            })
            content.append({'text': '', 'style': 'NORMAL_TEXT'})
        
        # Overall Comments
        overall = report_data.get('overall_comments', '')
        if overall:
            content.append({
                'text': 'OVERALL COMMENTS',
                'style': 'HEADING_2',
                'bold': True
            })
            content.append({
                'text': overall,
                'style': 'NORMAL_TEXT',
                'bold': False
            })
            content.append({'text': '', 'style': 'NORMAL_TEXT'})
        
        # Strengths
        strengths = report_data.get('strengths', [])
        if strengths:
            content.append({
                'text': 'STRENGTHS',
                'style': 'HEADING_2',
                'bold': True
            })
            for strength in strengths:
                content.append({
                    'text': f'  • {strength}',
                    'style': 'NORMAL_TEXT',
                    'bold': False
                })
            content.append({'text': '', 'style': 'NORMAL_TEXT'})
        
        # Weaknesses
        weaknesses = report_data.get('weaknesses', [])
        if weaknesses:
            content.append({
                'text': 'WEAKNESSES',
                'style': 'HEADING_2',
                'bold': True
            })
            for weakness in weaknesses:
                content.append({
                    'text': f'  • {weakness}',
                    'style': 'NORMAL_TEXT',
                    'bold': False
                })
            content.append({'text': '', 'style': 'NORMAL_TEXT'})
        
        # Character Notes
        character_notes = report_data.get('character_notes', '')
        if character_notes:
            content.append({
                'text': 'CHARACTER NOTES',
                'style': 'HEADING_2',
                'bold': True
            })
            content.append({
                'text': character_notes,
                'style': 'NORMAL_TEXT',
                'bold': False
            })
            content.append({'text': '', 'style': 'NORMAL_TEXT'})
        
        # Structure Analysis
        structure = report_data.get('structure_analysis', '')
        if structure:
            content.append({
                'text': 'STRUCTURE ANALYSIS',
                'style': 'HEADING_2',
                'bold': True
            })
            content.append({
                'text': structure,
                'style': 'NORMAL_TEXT',
                'bold': False
            })
            content.append({'text': '', 'style': 'NORMAL_TEXT'})
        
        # Market Positioning
        market = report_data.get('market_positioning', '')
        if market:
            content.append({
                'text': 'MARKET POSITIONING',
                'style': 'HEADING_2',
                'bold': True
            })
            content.append({
                'text': market,
                'style': 'NORMAL_TEXT',
                'bold': False
            })
            content.append({'text': '', 'style': 'NORMAL_TEXT'})
        
        # Evidence Quotes
        quotes = report_data.get('evidence_quotes', [])
        if quotes:
            content.append({
                'text': 'EVIDENCE QUOTES',
                'style': 'HEADING_2',
                'bold': True
            })
            for i, quote in enumerate(quotes, 1):
                quote_text = quote.get('quote', '')
                page = quote.get('page', 0)
                context = quote.get('context', '')
                
                content.append({
                    'text': f'{i}. Page {page}:',
                    'style': 'NORMAL_TEXT',
                    'bold': True
                })
                content.append({
                    'text': f'"{quote_text}"',
                    'style': 'NORMAL_TEXT',
                    'bold': False
                })
                if context:
                    content.append({
                        'text': f'Context: {context}',
                        'style': 'NORMAL_TEXT',
                        'bold': False
                    })
                content.append({'text': '', 'style': 'NORMAL_TEXT'})
        
        # Footer
        content.append({'text': '', 'style': 'NORMAL_TEXT'})
        content.append({
            'text': '---',
            'style': 'NORMAL_TEXT',
            'bold': False
        })
        content.append({
            'text': 'Generated by CoverageIQ - AI-powered script coverage analysis',
            'style': 'NORMAL_TEXT',
            'bold': False
        })
        
        return content


# Singleton instance
_exporter: Optional[GoogleDocsExporter] = None


def get_google_docs_exporter() -> GoogleDocsExporter:
    """Get or create the Google Docs exporter singleton.
    
    Returns:
        GoogleDocsExporter instance
    """
    global _exporter
    if _exporter is None:
        _exporter = GoogleDocsExporter()
    return _exporter
