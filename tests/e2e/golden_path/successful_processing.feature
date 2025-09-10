Feature: Golden Path - Successful File Processing
  As a user
  I want my files to process successfully without errors
  So that I can trust the system to handle my documents reliably

  Background:
    Given I have a clean working environment
    And the AI service is responding normally
    And I have sufficient disk space
    And all required dependencies are available

  @golden_path @critical @e2e
  Scenario: All files process successfully on first attempt
    Given I have 5 PDF files with valid content in the input directory
    And each file is under 50MB in size
    And I have proper read/write permissions on all directories
    When I run the document processing with default settings
    Then I should see "Processing 5 files..." in the progress display
    And all 5 files should process successfully without retries
    And the progress display should show "5 successful, 0 failed, 0 retries"
    And each file should appear in the processed directory with an AI-generated filename
    And the original files should be removed from the input directory
    And I should see a completion message indicating 100% success rate
    And the processing should complete in reasonable time (under 2 minutes)

  @golden_path @critical @e2e
  Scenario: Mixed file types process successfully together
    Given I have 2 PDF files in the input directory
    And I have 2 PNG image files in the input directory  
    And I have 1 TXT document in the input directory
    And all files contain valid, processable content
    When I run the document processing with OCR enabled
    Then I should see "Processing 5 files..." in the progress display
    And all 5 files should process successfully
    And PDF files should retain .pdf extensions with AI-generated names
    And PNG files should retain .png extensions with AI-generated names
    And TXT files should retain .txt extensions with AI-generated names
    And I should see appropriate processing messages for each file type
    And the final statistics should show "5 successful, 0 failed"
    And each file type should appear in the correctly organized folders

  @golden_path @critical @e2e
  Scenario: Files succeed after legitimate retries
    Given I have 3 PDF files in the input directory
    And 1 file is temporarily locked by antivirus scanning
    And the other 2 files are immediately available
    When I run the document processing
    Then I should see the 2 available files process immediately
    And I should see "Retrying locked file..." message for the third file
    And after the antivirus scan completes, the third file should process successfully
    And the final statistics should show "3 successful, 0 failed, 1 retry"
    And all 3 files should appear in the processed directory
    And I should see confirmation that all files were processed successfully
    
  @golden_path @cross_platform @e2e
  Scenario: Cross-platform consistency validation
    Given I am running on any supported platform (Windows/Linux/Mac)
    And I have 3 files with unicode characters in their names
    And the files contain international characters and symbols
    When I run the document processing
    Then all files should process successfully regardless of platform
    And the generated filenames should be compatible across all platforms
    And unicode characters should be handled appropriately for the filesystem
    And the progress display should show correctly formatted file names
    And all file operations should complete without encoding errors

  @golden_path @performance @e2e
  Scenario: Large batch processing maintains performance
    Given I have 25 small PDF files (under 5MB each) in the input directory
    And all files contain valid text content
    And I have enabled batch processing mode
    When I run the document processing
    Then processing should start immediately without delays
    And I should see continuous progress updates throughout processing
    And all 25 files should process successfully
    And the average processing time per file should be under 10 seconds
    And memory usage should remain stable throughout the batch
    And the final statistics should accurately show "25 successful, 0 failed"