Feature: Document Processing Workflow
  As a user
  I want to process my documents automatically
  So that they are organized with meaningful names

  Background:
    Given I have a clean working directory
    And the AI service is available

  @golden_path @critical @bdd
  Scenario: User processes documents successfully
    Given I have 3 PDF files in the input directory
    When I run the document processing
    Then I should see 3 files processed successfully
    And the progress display should show 100% completion
    And all files should appear in the processed directory with AI-generated names
    And I should see "Success" status for all files

  @error_condition @bdd
  Scenario: User encounters temporary file locks
    Given I have 2 PDF files in the input directory
    And one file is temporarily locked by antivirus
    When I run the document processing
    Then I should see 1 file processed immediately
    And 1 file should be retried and then succeed
    And the final statistics should show 2 successful files
    And I should see recovery statistics for the locked file

  @golden_path @bdd
  Scenario: User processes mixed file types successfully
    Given I have 1 PDF file in the input directory
    And I have 1 PNG file in the input directory
    And I have 1 TXT file in the input directory
    When I run the document processing
    Then I should see 3 files processed successfully
    And all files should maintain their original extensions
    And I should see appropriate processing messages for each file type

  @error_condition @bdd
  Scenario: User understands which files failed and why
    Given I have 2 valid PDF files in the input directory
    And I have 1 corrupted file in the input directory
    When I run the document processing
    Then I should see 2 files processed successfully
    And I should see 1 file failed with clear error message
    And the failed file should appear in the unprocessed directory
    And I should see accurate final statistics showing 2 success, 1 failure