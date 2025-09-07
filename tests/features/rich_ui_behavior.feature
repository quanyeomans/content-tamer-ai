Feature: Rich UI Display Consistency and Behavior
  As a user processing documents with Rich UI
  I want consistent, beautiful display behavior
  So that I can track progress and see processing history clearly

  Background:
    Given I have Rich UI enabled
    And I have a clean test environment

  @ui @regression @critical
  Scenario: File processing lines persist and accumulate during processing
    Given I am processing 3 documents with Rich UI
    When I start processing file "document1.pdf"
    And I complete processing file "document1.pdf" as "Analysis_Report.pdf"
    Then I should see file "document1.pdf → Analysis_Report.pdf" in the display
    
    When I start processing file "document2.pdf" 
    And I complete processing file "document2.pdf" as "Summary_Document.pdf"
    Then I should see file "document1.pdf → Analysis_Report.pdf" still displayed
    And I should see file "document2.pdf → Summary_Document.pdf" displayed below it
    
    When I start processing file "document3.pdf"
    And I complete processing file "document3.pdf" as "Final_Report.pdf"
    Then I should see all three completed files displayed persistently
    And the display should show proper completion statistics

  @ui @regression @critical  
  Scenario: Borders wrap content properly without fragmentation
    Given I am using Rich UI with progress display
    When I start processing 2 documents
    And I complete processing both documents successfully
    Then the UI borders should wrap all content properly
    And I should not see small rectangular border fragments
    And the completion panel should have full borders around statistics

  @ui @regression
  Scenario: Failed files appear in persistent display with error information
    Given I am processing 3 documents with Rich UI
    When I complete processing file "success1.pdf" successfully
    And I complete processing file "success2.pdf" successfully  
    And I fail processing file "corrupted.pdf" with error "File corrupted"
    Then I should see "success1.pdf" with success icon in the display
    And I should see "success2.pdf" with success icon in the display
    And I should see "corrupted.pdf" with error icon and "File corrupted" message
    And all three files should remain visible in the persistent display

  @ui @regression
  Scenario: Progress statistics remain accurate throughout processing
    Given I am processing 5 documents with Rich UI and statistics enabled
    When I complete 3 files successfully
    And I fail 2 files with errors
    Then the statistics should show "3 successful files"
    And the statistics should show "2 failed files" 
    And the statistics should show "60.0% success rate"
    And the elapsed time should be displayed correctly
    And the statistics panel should have proper borders

  @ui @regression
  Scenario: Display handles large number of completed files gracefully
    Given I am processing 8 documents with Rich UI
    When I complete all 8 files successfully
    Then the completed files display should show the last 5 files
    And older completed files should not overcrowd the display
    And the display should remain properly formatted
    And the progress bar should show 100% completion

  @ui @golden_path
  Scenario: Rich UI provides delightful user experience during normal processing
    Given I am a user with Rich UI enabled
    When I process 3 documents successfully
    Then I should see beautiful progress bars with colors
    And I should see clear file status indicators
    And I should see celebratory completion messages
    And I should see properly formatted statistics
    And the overall display should be professional and engaging

  @ui @error_condition
  Scenario: Rich UI handles errors gracefully without breaking display
    Given I am using Rich UI during processing
    When processing encounters various errors
    And some files succeed while others fail
    Then the Rich UI should maintain consistent formatting
    And error messages should be clearly displayed with appropriate styling
    And the progress display should continue working correctly
    And the final statistics should account for all outcomes

  @ui @performance
  Scenario: Rich UI remains responsive during intensive processing
    Given I am processing a large batch of 10 documents
    When processing is intensive and takes significant time
    Then the Rich UI should update smoothly without lag
    And the progress indicators should refresh consistently
    And the completed files list should update efficiently
    And the display should not cause performance degradation