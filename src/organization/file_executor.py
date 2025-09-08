"""
File Execution Module for Post-Processing Organization

This module handles the physical execution of organization plans:
- Creating target folder structures  
- Moving files to organized locations
- Handling collisions and errors gracefully
- Maintaining file integrity during moves
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from file_organizer import FileManager


class OrganizationFileExecutor:
    """Executes organization plans by physically moving files to target structure."""

    def __init__(self, target_folder: str):
        """
        Initialize file executor for target folder.
        
        Args:
            target_folder: Base directory where organization will be applied
        """
        self.target_folder = target_folder
        self.file_manager = FileManager()
        
    def execute_organization_plan(self, organization_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an organization plan by physically moving files.
        
        Args:
            organization_result: Result from organization engine containing structure and file assignments
            
        Returns:
            Execution results with success/failure details
        """
        if not organization_result.get('success', False):
            return {
                'success': False,
                'reason': 'Cannot execute failed organization plan',
                'files_moved': 0
            }
            
        organization_structure = organization_result.get('organization_structure', {})
        file_assignments = organization_structure.get('file_assignments', [])
        
        logging.info(f"Executing organization plan for {len(file_assignments)} files")
        
        # Step 1: Create folder structure (always create, even if no files to move)
        folder_creation_result = self._create_folder_structure(organization_structure)
        if not folder_creation_result['success']:
            return folder_creation_result
        
        # Step 2: Handle case with no files to move
        if not file_assignments:
            return {
                'success': True,
                'reason': 'No files to organize',
                'files_moved': 0,
                'files_failed': 0,
                'total_files': 0,
                'folders_created': folder_creation_result['folders_created'],
                'execution_summary': {
                    'total_files_processed': 0,
                    'files_successfully_moved': 0,
                    'files_failed_to_move': 0,
                    'success_rate': 0.0,
                    'folders_created': len(folder_creation_result['folders_created']),
                    'folder_creation_success': True,
                    'overall_success': True
                }
            }
        
        # Step 3: Execute file moves
        move_results = self._execute_file_moves(file_assignments)
        
        # Step 4: Generate comprehensive results
        execution_result = {
            'success': move_results['total_moves'] > 0 or len(file_assignments) == 0,
            'files_moved': move_results['successful_moves'],
            'files_failed': move_results['failed_moves'],
            'total_files': len(file_assignments),
            'folders_created': folder_creation_result['folders_created'],
            'move_details': move_results['move_details'],
            'execution_summary': self._generate_execution_summary(move_results, folder_creation_result)
        }
        
        if move_results['failed_moves'] > 0:
            execution_result['warnings'] = f"{move_results['failed_moves']} files failed to move"
        
        logging.info(f"Organization execution completed: {move_results['successful_moves']}/{len(file_assignments)} files moved")
        
        return execution_result
    
    def _create_folder_structure(self, organization_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Create the target folder structure."""
        folders = organization_structure.get('folders', {})
        hierarchy_type = organization_structure.get('hierarchy_type', 'category-first')
        
        folders_created = []
        folders_failed = []
        
        for folder_name, folder_info in folders.items():
            folder_path = os.path.join(self.target_folder, folder_name)
            
            try:
                # Create main folder
                os.makedirs(folder_path, exist_ok=True)
                folders_created.append(folder_name)
                logging.debug(f"Created folder: {folder_path}")
                
                # Create subfolders if they exist
                subfolders = folder_info.get('subfolders', {})
                for subfolder_name in subfolders.keys():
                    subfolder_path = os.path.join(folder_path, subfolder_name)
                    os.makedirs(subfolder_path, exist_ok=True)
                    folders_created.append(f"{folder_name}/{subfolder_name}")
                    logging.debug(f"Created subfolder: {subfolder_path}")
                    
            except (OSError, PermissionError) as e:
                error_msg = f"Failed to create folder {folder_name}: {e}"
                logging.error(error_msg)
                folders_failed.append({'folder': folder_name, 'error': str(e)})
        
        return {
            'success': len(folders_failed) == 0,
            'folders_created': folders_created,
            'folders_failed': folders_failed,
            'total_folders': len(folders)
        }
    
    def _execute_file_moves(self, file_assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the actual file moves according to assignments."""
        successful_moves = 0
        failed_moves = 0
        move_details = []
        
        for assignment in file_assignments:
            filename = assignment['filename']
            current_path = assignment['current_path']
            target_folder = assignment['target_folder']
            category = assignment['category']
            
            move_result = self._move_single_file(
                current_path=current_path,
                target_folder=target_folder,
                filename=filename,
                category=category
            )
            
            move_details.append(move_result)
            
            if move_result['success']:
                successful_moves += 1
            else:
                failed_moves += 1
        
        return {
            'successful_moves': successful_moves,
            'failed_moves': failed_moves,
            'total_moves': successful_moves + failed_moves,
            'move_details': move_details
        }
    
    def _move_single_file(self, current_path: str, target_folder: str, filename: str, category: str) -> Dict[str, Any]:
        """Move a single file to its target location."""
        try:
            # Validate source file exists
            if not os.path.exists(current_path):
                return {
                    'success': False,
                    'filename': filename,
                    'error': f'Source file does not exist: {current_path}',
                    'current_path': current_path,
                    'target_folder': target_folder
                }
            
            # Determine target path
            target_directory = os.path.join(self.target_folder, target_folder)
            
            # Ensure target directory exists
            os.makedirs(target_directory, exist_ok=True)
            
            # Handle filename collisions
            file_extension = os.path.splitext(filename)[1]
            base_filename = os.path.splitext(filename)[0]
            
            # Import FilenameHandler directly
            from file_organizer import FilenameHandler
            filename_handler = FilenameHandler()
            final_filename = filename_handler.handle_duplicate_filename(
                base_filename, target_directory, file_extension
            )
            
            target_path = os.path.join(target_directory, final_filename + file_extension)
            
            # Perform the move using safe_move
            self.file_manager.safe_move(current_path, target_path)
            
            logging.info(f"Moved {filename} -> {target_folder}/{final_filename}{file_extension}")
            
            return {
                'success': True,
                'filename': filename,
                'current_path': current_path,
                'target_path': target_path,
                'target_folder': target_folder,
                'final_filename': final_filename + file_extension,
                'category': category
            }
            
        except Exception as e:
            error_msg = f"Failed to move {filename} to {target_folder}: {e}"
            logging.error(error_msg)
            
            return {
                'success': False,
                'filename': filename,
                'current_path': current_path,
                'target_folder': target_folder,
                'error': str(e),
                'category': category
            }
    
    def _generate_execution_summary(self, move_results: Dict, folder_results: Dict) -> Dict[str, Any]:
        """Generate a comprehensive execution summary."""
        return {
            'total_files_processed': move_results['total_moves'],
            'files_successfully_moved': move_results['successful_moves'],
            'files_failed_to_move': move_results['failed_moves'],
            'success_rate': (
                move_results['successful_moves'] / move_results['total_moves'] 
                if move_results['total_moves'] > 0 else 0.0
            ),
            'folders_created': len(folder_results['folders_created']),
            'folder_creation_success': folder_results['success'],
            'overall_success': (
                folder_results['success'] and 
                move_results['successful_moves'] == move_results['total_moves']
            )
        }
    
    def get_current_organization_state(self) -> Dict[str, Any]:
        """Get current state of organization in target folder."""
        if not os.path.exists(self.target_folder):
            return {'organized': False, 'reason': 'Target folder does not exist'}
        
        # Scan for organized folder structure
        organized_folders = []
        files_in_root = []
        
        for item in os.listdir(self.target_folder):
            item_path = os.path.join(self.target_folder, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                # Check if this looks like an organized folder
                file_count = len([f for f in os.listdir(item_path) 
                                 if os.path.isfile(os.path.join(item_path, f))])
                organized_folders.append({
                    'name': item,
                    'files': file_count
                })
            elif os.path.isfile(item_path):
                files_in_root.append(item)
        
        return {
            'organized': len(organized_folders) > 0,
            'organized_folders': organized_folders,
            'files_in_root': len(files_in_root),
            'total_organized_folders': len(organized_folders)
        }
    
    def validate_organization_plan(self, organization_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an organization plan before execution."""
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check if organization result is valid
        if not organization_result.get('success', False):
            validation_result['valid'] = False
            validation_result['issues'].append('Organization plan failed to generate')
            return validation_result
        
        organization_structure = organization_result.get('organization_structure', {})
        file_assignments = organization_structure.get('file_assignments', [])
        
        # Check file assignments
        for assignment in file_assignments:
            current_path = assignment.get('current_path', '')
            
            # Validate source files exist
            if not os.path.exists(current_path):
                validation_result['warnings'].append(
                    f"Source file missing: {assignment.get('filename', 'unknown')}"
                )
        
        # Check target folder permissions
        try:
            test_folder = os.path.join(self.target_folder, 'test_write_permission')
            os.makedirs(test_folder, exist_ok=True)
            os.rmdir(test_folder)
        except (OSError, PermissionError):
            validation_result['valid'] = False
            validation_result['issues'].append(
                f'No write permission to target folder: {self.target_folder}'
            )
        
        return validation_result