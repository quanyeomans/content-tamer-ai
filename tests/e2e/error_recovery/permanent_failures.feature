Feature: Error Recovery - Permanent Failure Handling
  As a user
  I want to understand which files cannot be processed and why
  So that I can take appropriate action for problematic files

  Background:
    Given I have a clean working environment
    And error handling is properly configured
    And I have an unprocessed directory for failed files

  @error_recovery @permanent_failures @e2e
  Scenario: Corrupt files are properly identified and isolated
    Given I have 5 files in the input directory:
      | filename           | file_status    |
      | good_file_1.pdf    | valid          |
      | good_file_2.pdf    | valid          |
      | corrupted.pdf      | corrupted      |
      | good_file_3.pdf    | valid          |
      | empty_file.pdf     | empty          |
    When I run the document processing
    Then the 3 valid files should process successfully
    And I should see "File corrupted, moving to unprocessed..." for corrupted.pdf
    And I should see "File is empty, moving to unprocessed..." for empty_file.pdf
    And the corrupted files should be moved to the unprocessed directory
    And the final statistics should show "3 successful, 2 failed"
    And I should see detailed error explanations for each failed file
    And the error messages should be user-friendly and actionable

  @error_recovery @unsupported_formats @e2e
  Scenario: Unsupported file formats are handled gracefully
    Given I have 6 files in the input directory:
      | filename             | file_type      |
      | document.pdf         | supported      |
      | image.png           | supported      |
      | presentation.pptx   | unsupported    |
      | spreadsheet.xlsx    | unsupported    |
      | text_file.txt       | supported      |
      | unknown.xyz         | unknown        |
    When I run the document processing
    Then the 3 supported files should process successfully
    And I should see "Unsupported format: .pptx" for presentation.pptx
    And I should see "Unsupported format: .xlsx" for spreadsheet.xlsx
    And I should see "Unknown file type: .xyz" for unknown.xyz
    And unsupported files should be moved to the unprocessed directory
    And the final statistics should show "3 successful, 3 failed"
    And I should receive guidance on supported file formats
    And error messages should suggest alternative approaches for unsupported files

  @error_recovery @size_limits @e2e
  Scenario: Files exceeding size limits are handled appropriately
    Given I have 4 files in the input directory:
      | filename           | file_size     |
      | normal_file.pdf    | 5MB           |
      | large_file.pdf     | 150MB         |
      | huge_file.pdf      | 500MB         |
      | small_file.pdf     | 1MB           |
    And the maximum file size limit is set to 100MB
    When I run the document processing
    Then the 2 normal-sized files should process successfully
    And I should see "File too large (150MB > 100MB limit)" for large_file.pdf
    And I should see "File too large (500MB > 100MB limit)" for huge_file.pdf
    And oversized files should be moved to the unprocessed directory
    And the final statistics should show "2 successful, 2 failed"
    And I should receive guidance on handling large files
    And error messages should suggest file compression or splitting options

  @error_recovery @mixed_failures @e2e
  Scenario: Mixed permanent and recoverable failures are distinguished
    Given I have 8 files in the input directory:
      | filename              | issue_type           |
      | good_file_1.pdf       | none                |
      | temp_locked.pdf       | temporary_lock       |
      | corrupted.pdf         | permanent_corruption |
      | good_file_2.pdf       | none                |
      | oversized.pdf         | size_limit_exceeded  |
      | temp_network.pdf      | temporary_network    |
      | invalid_format.xyz    | unsupported_format   |
      | good_file_3.pdf       | none                |
    When I run the document processing
    Then the 3 good files should process immediately
    And temp_locked.pdf should retry and succeed after the lock is released
    And temp_network.pdf should retry and succeed after network recovery
    And corrupted.pdf should be moved to unprocessed as permanently failed
    And oversized.pdf should be moved to unprocessed as permanently failed
    And invalid_format.xyz should be moved to unprocessed as permanently failed
    And the final statistics should show "5 successful, 3 failed, 2 retries"
    And I should see clear categorization of temporary vs permanent failures
    And each failure type should have appropriate user guidance

  @error_recovery @ai_service_failures @e2e
  Scenario: Permanent AI service failures trigger appropriate fallbacks
    Given I have 3 files in the input directory
    And the AI service is completely unavailable with no recovery expected
    And fallback naming is configured
    When I run the document processing
    Then I should see "AI service unavailable, using fallback naming..." warning
    And all 3 files should still be processed using fallback strategies
    And files should receive meaningful names based on basic content analysis
    And I should see confirmation that fallback processing was used
    And the final statistics should show "3 successful, 0 failed"
    And I should understand that AI features were not available but processing continued
    And I should receive information about when AI services might be restored