Feature: Progress Display and User Feedback
  As a user
  I want to see clear progress during processing
  So that I know the system is working and can track completion

  @bdd @critical
  Scenario: User sees progress counters increment correctly
    Given I have a clean progress environment
    When I process 2 files successfully
    Then I should see the success counter increase by 2
    And I should see the total completed counter increase by 2
    And I should see 0 errors in the counter

  @bdd @golden_path
  Scenario: User sees accurate completion statistics
    Given I have a clean progress environment
    When I complete a full processing session with 3 successes and 1 failure
    Then I should see final statistics showing 3 successful files
    And I should see final statistics showing 1 failed file
    And I should see final statistics showing 4 total files processed
    And the success rate should be calculated correctly

  @bdd
  Scenario: User sees clear file status progression
    Given I have a clean progress environment
    When I track file processing status changes
    Then I should see files start in processing state
    And I should see files transition to completed state
    And I should see appropriate status messages throughout