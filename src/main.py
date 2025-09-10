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
    try:
        from interfaces.human.rich_console_manager import RichConsoleManager

        console_mgr = RichConsoleManager()
        main_console = console_mgr.console

        # Show welcome header  
        main_console.print()
        if hasattr(main_console, "options") and main_console.options.encoding == "utf-8":
            main_console.print("🎯 [bold blue]CONTENT TAMER AI[/bold blue]")
        else:
            main_console.print(">> [bold blue]CONTENT TAMER AI[/bold blue] <<")
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
            # Use orchestration layer for processing
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
                    main_console.print(":x: [red]Application kernel unavailable[/red]")
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
            main_console.print(":information_source: [yellow]Setup cancelled by user[/yellow]")
        return False

    except ImportError as e:
        if main_console:
            main_console.print(
                f":x: [red]Content Tamer AI startup failed:[/red] [white]{e}[/white]"
            )
            main_console.print()
            main_console.print("[yellow]Domain architecture components missing.[/yellow]")
        else:
            print(f"ERROR: Content Tamer AI startup failed: {e}")
            print("Domain architecture components missing.")
        return False

    except Exception as e:
        if main_console:
            main_console.print(f":x: [red]Application error:[/red] [white]{e}[/white]")
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

            console = RichConsoleManager().console
            console.print()
            console.print(":stop_button: [yellow]Operation cancelled by user[/yellow]")
        except ImportError:
            print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        # Use Rich Console for error if available
        try:
            from interfaces.human.rich_console_manager import RichConsoleManager

            console = RichConsoleManager().console
            console.print(f":collision: [red]Unexpected error:[/red] [white]{e}[/white]")
        except ImportError:
            print(f"Unexpected error: {e}")
        sys.exit(1)
