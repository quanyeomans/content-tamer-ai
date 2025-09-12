"""
Application Kernel

Main application coordination component that orchestrates all domain services
to implement complete user workflows following the persona-driven architecture.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..interfaces.base_interfaces import ProcessingResult
    from ..interfaces.programmatic.configuration_manager import ProcessingConfiguration

import datetime
import logging
import os
import shutil
import time
from dataclasses import dataclass

# Import display manager for Rich UI progress tracking
try:
    from shared.display.unified_display_manager import UnifiedDisplayManager
except ImportError:
    # Try with src prefix if running from outside src/
    from ..shared.display.unified_display_manager import UnifiedDisplayManager

# Import domain services
try:
    from domains.ai_integration.ai_integration_service import AIIntegrationService
    from domains.content.content_service import ContentService
    from domains.organization.organization_service import OrganizationService
except ImportError:
    # Graceful degradation if domain services not available
    ContentService = None
    AIIntegrationService = None
    OrganizationService = None

# Runtime imports with fallbacks
if not TYPE_CHECKING:
    try:
        from ..interfaces.base_interfaces import ProcessingResult
    except ImportError:
        try:
            from interfaces.base_interfaces import ProcessingResult
        except ImportError:
            # Fallback implementation
            @dataclass
            class ProcessingResult:
                success: bool
                files_processed: int
                files_failed: int
                output_directory: str
                errors: List[str]
                warnings: List[str]
                metadata: Dict[str, Any]

    try:
        from ..interfaces.programmatic.configuration_manager import ProcessingConfiguration
    except ImportError:
        try:
            from interfaces.programmatic.configuration_manager import ProcessingConfiguration
        except ImportError:
            # Fallback implementation
            @dataclass
            class ProcessingConfiguration:
                input_dir: str
                output_dir: str
                provider: str = "openai"
                model: Optional[str] = None
                api_key: Optional[str] = None
                organization_enabled: bool = False


class ApplicationKernel:
    """
    Main application kernel coordinating all domain services.

    Implements complete user workflows by orchestrating:
    - Content Domain: Document extraction and enhancement
    - AI Integration Domain: Provider management and filename generation
    - Organization Domain: Document clustering and folder organization
    """

    def __init__(self, container):
        """Initialize application kernel with dependency container.

        Args:
            container: ApplicationContainer for dependency injection
        """
        self.container = container
        self.logger = logging.getLogger(__name__)

        # Initialize display manager for Rich UI progress tracking
        self.display_manager = UnifiedDisplayManager()

        # Domain services will be created lazily
        self._content_service = None
        self._ai_service = None
        self._organization_service = None

    @property
    def content_service(self):
        """Get or create content service."""
        if self._content_service is None and ContentService is not None:
            self._content_service = self.container.create_content_service()
        return self._content_service

    @property
    def ai_service(self):
        """Get or create AI integration service."""
        if self._ai_service is None and AIIntegrationService is not None:
            self._ai_service = self.container.create_ai_integration_service()
        return self._ai_service

    def get_organization_service(self, target_folder: str):
        """Get organization service for specific target folder."""
        # Organization service is folder-specific, so create new instance
        if OrganizationService is not None:
            return self.container.create_organization_service(target_folder)
        return None

    def process_documents(self, config: "ProcessingConfiguration") -> "ProcessingResult":
        """Execute document processing workflow (public interface)."""
        return self.execute_processing(config)

    def validate_processing_config(self, config: "ProcessingConfiguration") -> List[str]:
        """Validate processing configuration (public interface)."""
        return self._validate_processing_config(config)

    def execute_processing(self, config: "ProcessingConfiguration") -> "ProcessingResult":
        """Execute complete document processing workflow.

        Args:
            config: Processing configuration

        Returns:
            ProcessingResult with processing outcome
        """
        start_time = time.time()

        try:
            # Validate configuration
            errors = self._validate_processing_config(config)
            if errors:
                return ProcessingResult(
                    success=False,
                    files_processed=0,
                    files_failed=0,
                    output_directory=config.output_dir,
                    errors=errors,
                    warnings=[],
                    metadata={"validation_failed": True},
                )

            # Find documents to process
            documents = self._discover_documents(config.input_dir)
            if not documents:
                return ProcessingResult(
                    success=True,
                    files_processed=0,
                    files_failed=0,
                    output_directory=config.output_dir,
                    errors=[],
                    warnings=["No supported documents found in input directory"],
                    metadata={"no_documents": True},
                )

            # Execute processing pipeline
            results = self._execute_processing_pipeline(documents, config)

            # Calculate processing time
            processing_time = time.time() - start_time
            results.metadata["processing_time"] = f"{processing_time:.2f}s"

            return results

        except Exception as e:
            self.display_manager.error(f"Processing execution failed: {e}")
            return ProcessingResult(
                success=False,
                files_processed=0,
                files_failed=0,
                output_directory=config.output_dir,
                errors=[str(e)],
                warnings=[],
                metadata={"kernel_error": str(e)},
            )

    def _validate_processing_config(self, config: "ProcessingConfiguration") -> List[str]:
        """Validate processing configuration."""
        errors = []

        # Check required paths
        if not config.input_dir or not os.path.exists(config.input_dir):
            errors.append(f"Input directory does not exist: {config.input_dir}")

        if not config.output_dir:
            errors.append("Output directory is required")
        else:
            # Try to create output directory
            try:
                os.makedirs(config.output_dir, exist_ok=True)
                if not os.access(config.output_dir, os.W_OK):
                    errors.append(f"Output directory is not writable: {config.output_dir}")
            except Exception as e:
                errors.append(f"Cannot create output directory: {config.output_dir} - {e}")

        # Validate AI provider
        if self.ai_service:
            provider_validation = self.ai_service.validate_provider_setup(
                config.provider, config.api_key
            )
            if not provider_validation["available"]:
                errors.append(f"AI provider {config.provider} is not available")
            elif config.provider != "local" and not provider_validation["api_key_valid"]:
                errors.append(f"Invalid or missing API key for {config.provider}")

        return errors

    def _discover_documents(self, input_dir: str) -> List[str]:
        """Discover processable documents in input directory."""
        supported_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"]
        documents = []

        try:
            for root, _dirs, files in os.walk(input_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()

                    if file_ext in supported_extensions:
                        documents.append(file_path)

            self.display_manager.info(f"Discovered {len(documents)} processable documents")
            return documents

        except Exception as e:
            self.display_manager.error(f"Document discovery failed: {e}")
            return []

    def _execute_processing_pipeline(
        self, documents: List[str], config: "ProcessingConfiguration"
    ) -> "ProcessingResult":
        """Execute the complete processing pipeline."""
        files_processed = 0
        files_failed = 0
        errors = []
        warnings = []
        processed_documents = []

        try:
            # Single progress bar for all processing phases
            self.display_manager.info("Starting document processing pipeline...")
            progress_id = self.display_manager.start_progress(
                "Processing documents"
            )
            
            total_files = len(documents)
            current_file = 0
            
            # Process each file through the complete pipeline
            for doc_path in documents:
                current_file += 1
                base_name = os.path.basename(doc_path)
                
                try:
                    # Phase 1: Extract content for this file
                    self.display_manager.update_progress(
                        progress_id,
                        current_file,
                        total_files,
                        f"[1/3] Extracting: {base_name}"
                    )
                    
                    if self.content_service:
                        # Process single document
                        content_result = self.content_service.process_document_complete(doc_path)
                    else:
                        # Legacy fallback
                        content_result = self._legacy_single_content_processing(doc_path, config)
                    
                    if not content_result.get("ready_for_ai", False):
                        errors.append(f"Content not ready for AI: {doc_path}")
                        files_failed += 1
                        continue
                    
                    # Phase 2: Generate AI filename
                    self.display_manager.update_progress(
                        progress_id,
                        current_file,
                        total_files,
                        f"[2/3] Analyzing: {base_name}"
                    )
                    
                    ai_content = content_result["ai_ready_content"]

                    # Generate filename using AI with retry logic
                    if self.ai_service:
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                filename_result = self.ai_service.generate_filename_with_ai(
                                    content=ai_content,
                                    original_filename=base_name,
                                    provider=config.provider,
                                    model=config.model,
                                    api_key=config.api_key,
                                )
                                
                                if filename_result.status.value == "success":
                                    # Phase 3: Move/organize file
                                    self.display_manager.update_progress(
                                        progress_id,
                                        current_file,
                                        total_files,
                                        f"[3/3] Organizing: {base_name}"
                                    )
                                    
                                    new_filename = filename_result.content
                                    new_path = os.path.join(config.output_dir, new_filename)
                                    
                                    # Ensure output directory exists
                                    os.makedirs(config.output_dir, exist_ok=True)
                                    
                                    # Move file
                                    shutil.move(doc_path, new_path)
                                    
                                    # Prepare for organization
                                    processed_documents.append(
                                        {
                                            "original_path": doc_path,
                                            "current_path": new_path,
                                            "filename": new_filename,
                                            "content": ai_content,
                                            "metadata": content_result.get("metadata", {}),
                                        }
                                    )
                                    
                                    files_processed += 1
                                    break  # Success, exit retry loop
                                else:
                                    if attempt < max_retries - 1:
                                        self.display_manager.warning(
                                            f"Retry {attempt + 1}/{max_retries} for {base_name}"
                                        )
                                        continue
                                    else:
                                        errors.append(
                                            f"AI filename generation failed for {doc_path}: {filename_result.error}"
                                        )
                                        files_failed += 1
                            except Exception as retry_error:
                                if attempt < max_retries - 1:
                                    self.display_manager.warning(
                                        f"Retry {attempt + 1}/{max_retries} for {base_name}: {retry_error}"
                                    )
                                    continue
                                else:
                                    raise
                    else:
                        # Fallback filename generation
                        self.display_manager.update_progress(
                            progress_id,
                            current_file,
                            total_files,
                            f"[3/3] Organizing: {base_name}"
                        )
                        processed_documents.append(
                            self._legacy_filename_generation(doc_path, content_result, config)
                        )
                        files_processed += 1
                        
                except Exception as e:
                    self.display_manager.error(
                        f"Processing failed for {base_name}: {e}"
                    )
                    errors.append(f"Processing error for {doc_path}: {e}")
                    files_failed += 1
            
            self.display_manager.finish_progress(progress_id)
            self.display_manager.success(
                f"Document processing completed - processed: {files_processed}, failed: {files_failed}"
            )

            # Phase 3: Organization (if enabled)
            organization_results = {}
            if config.organization_enabled and processed_documents:
                self.display_manager.info("Starting document organization...")
                org_progress = self.display_manager.start_progress(
                    "Phase 3: Organizing documents into folders"
                )

                org_service = self.get_organization_service(config.output_dir)
                if org_service:
                    # Update progress to show organization in progress
                    self.display_manager.update_progress(
                        org_progress, 1, 2, "Analyzing document content for clustering"
                    )

                    organization_results = org_service.organize_processed_documents(
                        processed_documents
                    )

                    # Complete progress
                    self.display_manager.update_progress(
                        org_progress, 2, 2, "Moving files to organized folders"
                    )

                    if organization_results.get("success"):
                        organized_files = organization_results.get("files_organized", 0)
                        self.display_manager.finish_progress(org_progress)
                        self.display_manager.success(
                            f"Successfully organized {organized_files} files into folders"
                        )
                    else:
                        org_error = organization_results.get("error", "Unknown organization error")
                        self.display_manager.finish_progress(org_progress)
                        self.display_manager.warning(f"Organization failed: {org_error}")
                        warnings.append(f"Organization failed: {org_error}")
                else:
                    self.display_manager.finish_progress(org_progress)
                    self.display_manager.warning("Organization service not available")
                    warnings.append("Organization service not available")

            # Show final processing status
            self.display_manager.print_separator()
            if files_processed > 0:
                if files_failed == 0:
                    self.display_manager.success(
                        f"Processing completed successfully! All {files_processed} files processed."
                    )
                else:
                    self.display_manager.warning(
                        f"Processing completed with mixed results: {files_processed} succeeded, {files_failed} failed."
                    )

                self.display_manager.info(f"Output directory: {config.output_dir}")

                if warnings:
                    self.display_manager.info("Warnings encountered:")
                    for warning in warnings[:3]:  # Show first 3 warnings
                        self.display_manager.warning(f"  • {warning}")
            else:
                self.display_manager.error(
                    "Processing failed - no files were processed successfully."
                )
                if errors:
                    self.display_manager.error("Errors encountered:")
                    for error in errors[:3]:  # Show first 3 errors
                        self.display_manager.error(f"  • {error}")
            self.display_manager.print_separator()

            # Compile final results
            return ProcessingResult(
                success=files_processed > 0,
                files_processed=files_processed,
                files_failed=files_failed,
                output_directory=config.output_dir,
                errors=errors,
                warnings=warnings,
                metadata={
                    "organization_enabled": config.organization_enabled,
                    "organization_results": organization_results,
                    "content_service_available": self.content_service is not None,
                    "ai_service_available": self.ai_service is not None,
                    "provider": config.provider,
                    "model": config.model,
                },
            )

        except Exception as e:
            self.display_manager.error(f"Processing pipeline failed: {e}")
            return ProcessingResult(
                success=False,
                files_processed=files_processed,
                files_failed=files_failed,
                output_directory=config.output_dir,
                errors=[str(e)],
                warnings=warnings,
                metadata={"pipeline_error": str(e)},
            )

    def _legacy_content_processing(
        self,
        documents: List[str],
        config: "ProcessingConfiguration",  # pylint: disable=unused-argument
        progress_id: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Fallback to legacy content processing when domain service not available."""
        self.display_manager.warning(
            "Using legacy content processing - domain service not available"
        )

        # Import domain content extraction service with fallback
        try:
            from ..domains.content.extraction_service import ExtractionService

            extraction_service = ExtractionService()
            results = {}

            # Use the new domain service with progress tracking
            total_docs = len(documents)
            for i, document in enumerate(documents, 1):
                # Update progress
                if progress_id:
                    self.display_manager.update_progress(
                        progress_id,
                        i,
                        total_docs,
                        f"Extracting content from {os.path.basename(document)}",
                    )

                extracted = extraction_service.extract_from_file(document)
                if extracted.quality.value != "failed" and extracted.text:
                    results[document] = {
                        "ai_ready_content": extracted.text,
                        "ready_for_ai": True,
                        "metadata": {"domain_extraction": True, "quality": extracted.quality.value},
                    }
                else:
                    results[document] = {
                        "ready_for_ai": False,
                        "error": extracted.error_message or "Extraction failed",
                    }
            return results

        except ImportError:
            # If domain service not available, return empty results
            return {
                doc: {
                    "ready_for_ai": False,
                    "error": "Content extraction service not available",
                }
                for doc in documents
            }

    def _legacy_single_content_processing(
        self, doc_path: str, config: "ProcessingConfiguration"
    ) -> Dict[str, Any]:
        """Process a single document with legacy extraction service."""
        try:
            from ..domains.content.extraction_service import ExtractionService
            
            extraction_service = ExtractionService()
            extracted = extraction_service.extract_from_file(doc_path)
            
            if extracted and extracted.quality.value != "failed":
                return {
                    "ready_for_ai": True,
                    "ai_ready_content": extracted.text or "",
                    "metadata": extracted.metadata or {},
                    "extraction": extracted,
                }
            else:
                return {
                    "ready_for_ai": False,
                    "error": extracted.error_message or "Extraction failed",
                }
        except ImportError:
            return {
                "ready_for_ai": False,
                "error": "Content extraction service not available",
            }
    
    def _legacy_filename_generation(
        self, file_path: str, content_result: Dict[str, Any], config: "ProcessingConfiguration"
    ) -> Dict[str, Any]:
        """Fallback filename generation when AI service not available."""
        # Simple fallback filename
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        new_filename = f"{base_name}_{timestamp}.pdf"

        new_path = os.path.join(config.output_dir, new_filename)

        # Move file
        import shutil

        os.makedirs(config.output_dir, exist_ok=True)
        shutil.move(file_path, new_path)

        return {
            "original_path": file_path,
            "current_path": new_path,
            "filename": new_filename,
            "content": content_result.get("ai_ready_content", ""),
            "metadata": {"legacy_filename": True},
        }

    def get_progress_status(self) -> Dict[str, Any]:
        """Get current processing progress status."""
        return {
            "status": "ready",  # This could be enhanced with actual progress tracking
            "services_available": {
                "content": self.content_service is not None,
                "ai_integration": self.ai_service is not None,
                "organization": OrganizationService is not None,
            },
        }

    def get_ai_providers(self) -> List[str]:
        """Get list of available AI providers."""
        if self.ai_service:
            return self.ai_service.provider_service.get_available_providers()
        else:
            # Fallback provider list
            return ["openai", "claude", "gemini"]

    def get_provider_models(self, provider: str) -> List[str]:
        """Get supported models for a provider."""
        if self.ai_service:
            return self.ai_service.provider_service.get_supported_models(provider)
        else:
            # Fallback model lists
            fallback_models = {
                "openai": ["gpt-4o", "gpt-4o-mini"],
                "claude": ["claude-3.5-sonnet", "claude-3.5-haiku"],
                "gemini": ["gemini-2.0-flash", "gemini-1.5-pro"],
            }
            return fallback_models.get(provider, [])

    def validate_provider_api_key(self, provider: str, api_key: str) -> bool:
        """Validate API key for a provider."""
        if self.ai_service:
            return self.ai_service.provider_service.validate_api_key(provider, api_key)
        else:
            # Basic validation - just check it's not empty
            return bool(api_key and api_key.strip())

    def get_system_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive system capabilities."""
        capabilities = {
            "domain_services": {
                "content": self.content_service is not None,
                "ai_integration": self.ai_service is not None,
                "organization": OrganizationService is not None,
            }
        }

        # Add AI provider capabilities
        if self.ai_service:
            capabilities["ai_providers"] = self.ai_service.get_provider_capabilities()

        # Add content processing capabilities
        if self.content_service:
            capabilities["content_processing"] = self.content_service.get_service_capabilities()

        return capabilities

    def health_check(self) -> Dict[str, Any]:
        """Perform application health check."""
        health = {
            "healthy": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "issues": [],
            "warnings": [],
        }

        # Check domain services
        if self.content_service is None:
            health["warnings"].append("Content service not available")

        if self.ai_service is None:
            health["warnings"].append("AI integration service not available")
            health["healthy"] = False

        # Check AI provider availability
        if self.ai_service:
            providers = self.ai_service.provider_service.get_available_providers()
            if not providers:
                health["issues"].append("No AI providers available")
                health["healthy"] = False

        # Check file system permissions
        try:
            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = os.path.join(temp_dir, "test.txt")
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
        except Exception as e:
            health["issues"].append(f"File system access problem: {e}")
            health["healthy"] = False

        return health
