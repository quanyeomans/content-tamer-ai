"""
Content Tamer AI - Intelligent Document Organization System

Main entry point routing through persona-driven interface architecture.

Originally based on sort-rename-move-pdf by munir-abbasi
(https://github.com/munir-abbasi/sort-rename-move-pdf)
Substantially modified and extended for multi-format content processing
and AI-powered document intelligence.

Licensed under MIT License - see LICENSE file for details.
"""

import sys

# Public API - only main function is exported
__all__ = ["main"]


def main():
    """
    Main entry point using clean persona-driven interface architecture.

    Routes to appropriate interface based on:
    - Interactive vs automation context detection
    - Command line arguments analysis
    - User persona requirements
    """
    # Initialize Rich Console for all output
    main_console = None
    emoji_handler = None
    try:
        from interfaces.human.rich_console_manager import RichConsoleManager
        from shared.display.emoji_handler import SmartEmojiHandler

        console_mgr = RichConsoleManager()
        main_console = console_mgr.console
        emoji_handler = SmartEmojiHandler(main_console)

        # Show welcome header  
        main_console.print()
        target_emoji = emoji_handler.get("🎯")
        main_console.print(f"{target_emoji} [bold blue]CONTENT TAMER AI[/bold blue]")
        main_console.print("[cyan]Intelligent Document Organization System[/cyan]")
        main_console.print()

    except ImportError:
        # Fallback if Rich not available
        print("Content Tamer AI - Intelligent Document Organization System")
        print()

    try:
        # Direct use of interface layer - no compatibility needed
        from interfaces.human.interactive_cli import InteractiveCLI

        cli = InteractiveCLI()
        args = cli.run_interactive_setup()

        if args:
            # Check if this is a setup/management command that doesn't need processing
            if hasattr(args, 'command_type') and args.command_type == 'setup':
                # Handle setup commands (like --setup-local-llm)
                from shared.infrastructure.model_manager import ModelManager
                from shared.infrastructure.dependency_manager import DependencyManager
                
                if args.setup_local_llm:
                    # Interactive setup for local LLM
                    dep_manager = DependencyManager()
                    model_manager = ModelManager()
                    
                    # Check and setup Ollama
                    if main_console:
                        main_console.print("\n[bold cyan]Setting up Local LLM...[/bold cyan]")
                        main_console.print("Checking for Ollama installation...")
                    
                    ollama_path = dep_manager.find_dependency("ollama")
                    if not ollama_path:
                        if main_console:
                            main_console.print("[red]Ollama is not installed.[/red]")
                            main_console.print("Please install Ollama from: https://ollama.ai")
                        return False
                    
                    if main_console:
                        check_emoji = emoji_handler.get("✅") if emoji_handler else "[OK]"
                        main_console.print(f"[green]{check_emoji} Ollama found at: {ollama_path}[/green]")
                        main_console.print("\nAvailable models for your system:")
                    
                    # List available models
                    models = model_manager.list_available_models()
                    for model in models:
                        if main_console:
                            main_console.print(f"  - {model.name}: {model.description}")
                    
                    # Recommend a model
                    recommended = model_manager.recommend_model()
                    if main_console and recommended:
                        main_console.print(f"\n[bold green]Recommended model: {recommended.name}[/bold green]")
                        main_console.print("This model is optimized for your system's capabilities.")
                    
                    return True
                    
                elif args.list_local_models:
                    model_manager = ModelManager()
                    models = model_manager.list_available_models()
                    if main_console:
                        main_console.print("\n[bold cyan]Available Local Models:[/bold cyan]")
                        for model in models:
                            main_console.print(f"  - {model.name}: {model.description}")
                    return True
                    
                elif args.check_local_requirements:
                    dep_manager = DependencyManager()
                    ollama_path = dep_manager.find_dependency("ollama")
                    if main_console:
                        if ollama_path:
                            check_emoji = emoji_handler.get("✅") if emoji_handler else "[OK]"
                            main_console.print(f"[green]{check_emoji} Ollama is installed at: {ollama_path}[/green]")
                        else:
                            error_emoji = emoji_handler.get("❌") if emoji_handler else "[X]"
                            main_console.print(f"[red]{error_emoji} Ollama is not installed[/red]")
                            main_console.print("Install from: https://ollama.ai")
                    return True
                    
                elif args.download_model:
                    model_manager = ModelManager()
                    success = model_manager.download_model(args.download_model)
                    return success
                    
                elif args.remove_model:
                    model_manager = ModelManager()
                    success = model_manager.remove_model(args.remove_model)
                    return success
                    
                else:
                    # Other setup commands
                    return True
            
            # Check if this is a list/info command that doesn't need processing
            if hasattr(args, 'list_models') and args.list_models:
                from domains.ai_integration.provider_registry import ProviderRegistry
                registry = ProviderRegistry()
                registry.list_all_models()
                return True
            
            # Check for dependency management commands
            if hasattr(args, 'check_dependencies') and args.check_dependencies:
                from shared.infrastructure.dependency_manager import DependencyManager
                dep_manager = DependencyManager()
                dep_manager.check_all_dependencies()
                return True
            
            if hasattr(args, 'refresh_dependencies') and args.refresh_dependencies:
                from shared.infrastructure.dependency_manager import DependencyManager
                dep_manager = DependencyManager()
                dep_manager.refresh_all_dependencies()
                return True
                
            # Regular document processing
            from core.application_container import ApplicationContainer
            from interfaces.programmatic.configuration_manager import ProcessingConfiguration

            # Create configuration from args
            config = ProcessingConfiguration(
                input_dir=args.input_dir or "./data/input",
                output_dir=args.output_dir or "./data/processed",
                provider=args.provider,
                model=args.model,
                api_key=args.api_key,
                organization_enabled=args.organize,
                quiet_mode=args.quiet_mode,
            )

            # Execute through kernel
            container = ApplicationContainer()
            kernel = container.create_application_kernel()

            if kernel is None:
                if main_console:
                    error_emoji = emoji_handler.get("❌") if emoji_handler else "[X]"
                    main_console.print(f"{error_emoji} [red]Application kernel unavailable[/red]")
                    main_console.print("[yellow]Domain architecture components missing.[/yellow]")
                else:
                    print(
                        "ERROR: Application kernel unavailable. Domain architecture components missing."
                    )
                return False

            result = kernel.execute_processing(config)

            # Show results with smart emoji usage (correct Rich pattern)
            if main_console and not config.quiet_mode:
                main_console.print()
                if result.success:
                    if (
                        hasattr(main_console, "options")
                        and main_console.options.encoding == "utf-8"
                    ):
                        main_console.print(
                            "🎉 [bold green]Processing completed successfully![/bold green]"
                        )
                        main_console.print(
                            f"📁 [cyan]Files processed:[/cyan] [white]{result.files_processed}[/white]"
                        )
                        main_console.print(
                            f"📂 [cyan]Output location:[/cyan] [white]{result.output_directory}[/white]"
                        )
                    else:
                        main_console.print(
                            ">> [bold green]Processing completed successfully![/bold green] <<"
                        )
                        main_console.print(
                            f"[✓] [cyan]Files processed:[/cyan] [white]{result.files_processed}[/white]"
                        )
                        main_console.print(
                            f"[>>] [cyan]Output location:[/cyan] [white]{result.output_directory}[/white]"
                        )
                else:
                    if (
                        hasattr(main_console, "options")
                        and main_console.options.encoding == "utf-8"
                    ):
                        main_console.print("❌ [bold red]Processing failed[/bold red]")
                        for error in result.errors[:3]:
                            main_console.print(f"   • [white]{error}[/white]")
                    else:
                        main_console.print(">> [bold red]Processing failed[/bold red] <<")
                        for error in result.errors[:3]:
                            main_console.print(f"   * [white]{error}[/white]")

            return result.success

        if main_console:
            info_emoji = emoji_handler.get("ℹ️") if emoji_handler else "[INFO]"
            main_console.print(f"{info_emoji} [yellow]Setup cancelled by user[/yellow]")
        return False

    except ImportError as e:
        if main_console:
            error_emoji = emoji_handler.get("❌") if emoji_handler else "[X]"
            main_console.print(
                f"{error_emoji} [red]Content Tamer AI startup failed:[/red] [white]{e}[/white]"
            )
            main_console.print()
            main_console.print("[yellow]Domain architecture components missing.[/yellow]")
        else:
            print(f"ERROR: Content Tamer AI startup failed: {e}")
            print("Domain architecture components missing.")
        return False

    except Exception as e:
        if main_console:
            error_emoji = emoji_handler.get("❌") if emoji_handler else "[X]"
            main_console.print(f"{error_emoji} [red]Application error:[/red] [white]{e}[/white]")
        else:
            print(f"ERROR: Application error: {e}")
        return False


# Backwards compatibility for direct execution
if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        # Use Rich Console for interrupt message if available
        try:
            from interfaces.human.rich_console_manager import RichConsoleManager

            console_mgr = RichConsoleManager()
            console = console_mgr.console
            from shared.display.emoji_handler import SmartEmojiHandler
            stop_emoji_handler = SmartEmojiHandler(console)
            stop_emoji = stop_emoji_handler.get("🛑")
            console.print()
            console.print(f"{stop_emoji} [yellow]Operation cancelled by user[/yellow]")
        except ImportError:
            print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        # Use Rich Console for error if available
        try:
            from interfaces.human.rich_console_manager import RichConsoleManager

            console_mgr = RichConsoleManager()
            console = console_mgr.console
            from shared.display.emoji_handler import SmartEmojiHandler
            error_emoji_handler = SmartEmojiHandler(console)
            error_emoji = error_emoji_handler.get("💥")
            console.print(f"{error_emoji} [red]Unexpected error:[/red] [white]{e}[/white]")
        except ImportError:
            print(f"Unexpected error: {e}")
        sys.exit(1)
