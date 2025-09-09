"""
Application Kernel

Main application coordination component that orchestrates all domain services
to implement complete user workflows following the persona-driven architecture.
"""

from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..interfaces.base_interfaces import ProcessingResult
    from ..interfaces.programmatic.configuration_manager import ProcessingConfiguration
import logging
import time
import datetime
import shutil
import os
from dataclasses import dataclass

# Import domain services
try:
    from domains.content.content_service import ContentService
    from domains.ai_integration.ai_integration_service import AIIntegrationService
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
            self.logger.error(f"Processing execution failed: {e}")
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
            for root, dirs, files in os.walk(input_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()

                    if file_ext in supported_extensions:
                        documents.append(file_path)

            self.logger.info(f"Discovered {len(documents)} processable documents")
            return documents

        except Exception as e:
            self.logger.error(f"Document discovery failed: {e}")
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
            # Phase 1: Content Extraction and Enhancement
            self.logger.info("Phase 1: Content extraction and enhancement...")

            if self.content_service:
                content_results = self.content_service.batch_process_documents(
                    documents,
                    {doc: None for doc in documents},  # Empty content map for fresh extraction
                )
            else:
                # Fallback to legacy content processing
                content_results = self._legacy_content_processing(documents, config)

            # Phase 2: AI Filename Generation
            self.logger.info("Phase 2: AI filename generation...")

            for file_path, content_result in content_results.items():
                try:
                    if content_result.get("ready_for_ai", False):
                        ai_content = content_result["ai_ready_content"]

                        # Generate filename using AI
                        if self.ai_service:
                            filename_result = self.ai_service.generate_filename_with_ai(
                                content=ai_content,
                                original_filename=os.path.basename(file_path),
                                provider=config.provider,
                                model=config.model,
                                api_key=config.api_key,
                            )

                            if filename_result.status.value == "success":
                                # Move file with new name
                                new_filename = filename_result.content
                                new_path = os.path.join(config.output_dir, new_filename)

                                # Ensure output directory exists
                                os.makedirs(config.output_dir, exist_ok=True)

                                # Move file
                                shutil.move(file_path, new_path)

                                # Prepare for organization
                                processed_documents.append(
                                    {
                                        "original_path": file_path,
                                        "current_path": new_path,
                                        "filename": new_filename,
                                        "content": ai_content,
                                        "metadata": content_result.get("metadata", {}),
                                    }
                                )

                                files_processed += 1
                            else:
                                errors.append(
                                    f"AI filename generation failed for {file_path}: {filename_result.error}"
                                )
                                files_failed += 1
                        else:
                            # Fallback filename generation
                            processed_documents.append(
                                self._legacy_filename_generation(file_path, content_result, config)
                            )
                            files_processed += 1
                    else:
                        errors.append(f"Content not ready for AI processing: {file_path}")
                        files_failed += 1

                except Exception as e:
                    self.logger.error(f"Processing failed for {file_path}: {e}")
                    errors.append(f"Processing error for {file_path}: {e}")
                    files_failed += 1

            # Phase 3: Organization (if enabled)
            organization_results = {}
            if config.organization_enabled and processed_documents:
                self.logger.info("Phase 3: Document organization...")

                org_service = self.get_organization_service(config.output_dir)
                if org_service:
                    organization_results = org_service.organize_processed_documents(
                        processed_documents
                    )

                    if organization_results.get("success"):
                        organized_files = organization_results.get("files_organized", 0)
                        self.logger.info(f"Successfully organized {organized_files} files")
                    else:
                        org_error = organization_results.get("error", "Unknown organization error")
                        warnings.append(f"Organization failed: {org_error}")
                else:
                    warnings.append("Organization service not available")

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
            self.logger.error(f"Processing pipeline failed: {e}")
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
        self, documents: List[str], config: "ProcessingConfiguration"
    ) -> Dict[str, Dict[str, Any]]:
        """Fallback to legacy content processing when domain service not available."""
        self.logger.warning("Using legacy content processing - domain service not available")

        results = {}
        for file_path in documents:
            try:
                # Import legacy content processing with fallback
                try:
                    from ..shared.file_operations.content_processor_factory import (
                        ContentProcessorFactory,
                    )
                except ImportError:
                    try:
                        from content_processors import ContentProcessorFactory
                    except ImportError:
                        # If content processors not available, return empty results
                        return {
                            doc: {
                                "ready_for_ai": False,
                                "error": "Content processors not available",
                            }
                            for doc in documents
                        }

                processor = ContentProcessorFactory.get_processor(file_path)
                if processor:
                    text, image_b64 = processor.extract_content(file_path)

                    results[file_path] = {
                        "ai_ready_content": text,
                        "ready_for_ai": bool(text and not text.startswith("Error:")),
                        "metadata": {"legacy_processing": True},
                    }
                else:
                    results[file_path] = {"ready_for_ai": False, "error": "No processor available"}

            except Exception as e:
                results[file_path] = {"ready_for_ai": False, "error": str(e)}

        return results

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
