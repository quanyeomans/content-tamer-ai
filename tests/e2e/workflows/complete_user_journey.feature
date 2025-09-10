Feature: Complete User Workflows - End-to-End User Journey
  As a user
  I want to experience a complete, intuitive workflow from start to finish
  So that I can confidently use the system for my document processing needs

  Background:
    Given I am a new user setting up the system for the first time
    And I have proper permissions on my directories
    And I have an internet connection for AI services

  @workflow @new_user @critical @e2e
  Scenario: First-time user complete workflow
    Given I have just installed the content-tamer-ai application
    And I have 5 mixed documents (PDF, PNG, TXT) to process
    And I have not configured any settings yet
    When I run the application for the first time
    Then I should see a welcome message and setup instructions
    And I should be guided through the initial configuration process
    And I should be able to set my preferred AI provider
    And I should be able to configure my input and output directories
    When I add my 5 files to the input directory
    And I run the document processing
    Then I should see clear progress indicators throughout the process
    And all 5 files should process successfully with meaningful names
    And I should see a completion summary with statistics
    And I should understand where my processed files are located
    And I should see suggestions for next steps or advanced features

  @workflow @expert_user @e2e
  Scenario: Expert user configuration and processing workflow
    Given I am an experienced user who wants custom settings
    And I have 10 documents with specific processing requirements
    When I run the application with expert mode
    Then I should see advanced configuration options
    And I should be able to customize filename generation patterns
    And I should be able to set custom retry policies
    And I should be able to configure organization preferences
    And I should be able to set custom AI provider settings
    When I configure my expert settings for my specific needs
    And I add my 10 files to the input directory
    And I run the document processing
    Then all files should process according to my expert configuration
    And I should see my custom settings reflected in the processing
    And I should see detailed progress with expert-level information
    And the final results should match my configuration expectations
    And I should be able to save my expert configuration for future use

  @workflow @error_understanding @e2e
  Scenario: User encounters and understands errors workflow
    Given I have 8 files in the input directory with various issues:
      | filename           | issue                    |
      | good_file_1.pdf    | none                    |
      | locked_file.pdf    | temporarily_locked      |
      | corrupted.pdf      | corrupted_content       |
      | good_file_2.pdf    | none                    |
      | oversized.pdf      | exceeds_size_limit      |
      | unsupported.pptx   | unsupported_format      |
      | good_file_3.pdf    | none                    |
      | network_fail.pdf   | temporary_network_issue |
    When I run the document processing
    Then I should see immediate processing of the 3 good files
    And I should see clear, understandable error messages for each problem
    And I should see retry attempts for temporary issues (locked_file.pdf, network_fail.pdf)
    And I should see permanent failures moved to unprocessed with explanations
    And the final summary should clearly categorize:
      | category           | count | files                                    |
      | successful         | 5     | 3 good files + 2 recovered files       |
      | permanent_failures | 3     | corrupted, oversized, unsupported       |
    And I should receive actionable guidance for each type of failure
    And I should understand what I can do about the failed files
    And I should feel confident about the successful processing

  @workflow @batch_processing @e2e
  Scenario: Large batch processing user workflow  
    Given I am processing a large batch of 50 documents
    And the documents include various file types and sizes
    And some documents may have temporary processing issues
    When I run the document processing in batch mode
    Then I should see an estimated time for completion
    And I should see continuous progress updates throughout the batch
    And I should be able to monitor the processing without constant attention
    And the system should handle temporary failures with automatic retries
    And I should receive periodic status updates for long-running processing
    And if I need to cancel, I should be able to stop gracefully
    When processing completes
    Then I should see a comprehensive final report including:
      | metric                    | information                              |
      | total_processed          | exact count of successful files          |
      | processing_time          | total time and average per file          |
      | retry_statistics         | how many files needed retries and why    |
      | failure_breakdown        | categorized list of failed files        |
      | recommendations          | suggestions for failed files            |
    And I should understand the overall success rate
    And I should know exactly where to find all processed files

  @workflow @incremental_processing @e2e
  Scenario: Incremental processing workflow with mixed results
    Given I have already processed some files successfully in previous sessions
    And I am adding 6 new files to process incrementally
    And my previous processing settings and preferences are saved
    When I add the new files to the input directory
    And I run incremental processing
    Then the system should recognize this is an incremental run
    And it should use my previously saved preferences automatically
    And it should only process the new files, not reprocess existing ones
    And I should see progress that clearly indicates incremental processing
    And the new files should integrate seamlessly with my existing organization
    When processing completes
    Then the new files should be organized consistently with my existing structure
    And I should see an incremental processing summary
    And my overall document collection should remain well-organized
    And I should understand the relationship between new and existing processed files