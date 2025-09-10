Feature: Error Recovery - Temporary Failure Recovery
  As a user
  I want the system to recover gracefully from temporary issues
  So that my files still get processed despite transient problems

  Background:
    Given I have a clean working environment
    And retry mechanisms are enabled
    And I have proper permissions on all directories

  @error_recovery @critical @e2e
  Scenario: Temporary file lock recovery (antivirus scanning)
    Given I have 3 PDF files in the input directory
    And the first file is temporarily locked by antivirus scanning
    And the antivirus will release the lock after 30 seconds
    When I run the document processing
    Then I should see the other 2 files process immediately
    And I should see "File temporarily locked, will retry..." for the first file
    And the system should wait and retry the locked file
    And after the antivirus releases the lock, the file should process successfully
    And the final statistics should show "3 successful, 0 failed, 1 retry"
    And all 3 files should appear in the processed directory
    And I should see clear communication about the temporary lock and recovery

  @error_recovery @critical @e2e
  Scenario: Network failure with AI API fallback recovery
    Given I have 4 PDF files in the input directory
    And the primary AI service becomes temporarily unavailable
    And a fallback naming strategy is configured
    When I run the document processing
    Then I should see "Primary AI service unavailable, using fallback..." message
    And the system should switch to fallback naming automatically
    And all 4 files should still be processed successfully
    And files should receive meaningful fallback names based on content analysis
    And I should see confirmation that fallback naming was used
    And when the primary AI service recovers, subsequent files should use it again
    And the final statistics should show "4 successful, 0 failed, 0 retries"

  @error_recovery @resilience @e2e
  Scenario: Multiple concurrent temporary failures resolve correctly
    Given I have 5 files in the input directory
    And 2 files are temporarily locked by different processes
    And 1 file encounters a temporary network issue during AI processing
    And the other 2 files are immediately available
    When I run the document processing with concurrent processing enabled
    Then the 2 available files should process immediately
    And I should see appropriate retry messages for each type of temporary failure
    And the system should retry each failed file with appropriate delays
    And all temporary issues should resolve within the retry timeout period
    And all 5 files should eventually process successfully
    And the final statistics should show "5 successful, 0 failed, 3 retries"
    And I should see a summary of recovery actions taken

  @error_recovery @permissions @e2e
  Scenario: Permission error recovery workflow
    Given I have 3 files in the input directory
    And 1 file has temporary permission restrictions
    And the permissions will be restored automatically after processing starts
    When I run the document processing
    Then the 2 accessible files should process immediately
    And I should see "Permission denied, will retry with elevated access..." for the restricted file
    And the system should attempt permission recovery strategies
    And when permissions are restored, the file should process successfully
    And all 3 files should appear in the processed directory
    And I should see clear explanation of the permission issue and resolution
    And the user should understand what happened and why it was resolved

  @error_recovery @disk_space @e2e
  Scenario: Temporary disk space shortage recovery
    Given I have 4 large PDF files (20MB each) in the input directory
    And the disk space is nearly full but will be freed during processing
    And cleanup processes will free space as files are processed
    When I run the document processing
    Then I should see "Low disk space detected, monitoring..." warning
    And the system should process files one at a time to conserve space
    And as space is freed, processing should continue normally
    And all 4 files should process successfully despite initial space constraints
    And I should see disk space monitoring messages throughout processing
    And the final statistics should show all files processed successfully
    And I should receive guidance about disk space management