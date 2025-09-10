Feature: Retry Success Determination Workflow
  As a user
  I want to clearly understand when files succeed after retries
  So that I don't mistakenly think successful files have failed

  Background:
    Given I have a clean working environment
    And retry mechanisms are properly configured
    And I have clear display settings enabled

  @workflow @critical @regression @e2e
  Scenario: Files that succeed after retries show as successes (Critical Bug Prevention)
    # This scenario specifically addresses the 2-hour debugging bug from TESTING_STRATEGY.md
    Given I have 5 files in the input directory
    And 2 files will encounter temporary issues requiring retries
    And 3 files will process successfully on first attempt
    When I run the document processing
    Then I should see the 3 immediately available files process first
    And they should show as "Processing..." then "Success" in the display
    And I should see the 2 problem files show as "Retrying..." 
    And after the retry attempts succeed, those files should show as "Success"
    And the progress statistics should update correctly throughout:
      | stage                  | success_count | failed_count | retry_count |
      | after_first_3_files   | 3             | 0            | 0           |
      | during_retries        | 3             | 0            | 2           |
      | after_retry_success   | 5             | 0            | 2           |
    And the final display should show "5 successful, 0 failed, 2 retries"
    And ALL files should appear in the processed directory, not unprocessed
    And the user should clearly understand that all files were ultimately successful

  @workflow @retry_communication @e2e
  Scenario: User understands retry process and outcomes clearly
    Given I have 6 files in the input directory
    And 3 files will have different types of temporary issues:
      | filename        | issue_type           | retry_outcome |
      | file1.pdf       | temporary_lock       | succeeds      |
      | file2.pdf       | network_timeout      | succeeds      |
      | file3.pdf       | permission_delay     | succeeds      |
    And 3 files will process normally
    When I run the document processing
    Then I should see clear, real-time communication about the retry process:
      | message_type              | example_message                               |
      | initial_failure          | "file1.pdf temporarily locked, will retry"   |
      | retry_attempt            | "Retrying file1.pdf (attempt 1 of 3)..."     |
      | retry_success            | "file1.pdf processed successfully on retry"  |
      | different_failure_types  | "file2.pdf network timeout, will retry"      |
    And I should understand that retries are normal and expected
    And I should see progress that clearly distinguishes between:
      | status_type           | visual_indicator        |
      | immediate_success     | "✓ Success"            |
      | retry_in_progress     | "⟳ Retrying..."        |
      | retry_success         | "✓ Success (retried)"  |
    And the final summary should celebrate all successes equally
    And I should not feel concerned about files that needed retries

  @workflow @retry_vs_failure @e2e
  Scenario: User clearly distinguishes retries from permanent failures
    Given I have 9 files in the input directory with mixed outcomes:
      | filename           | issue_type              | final_outcome    |
      | success1.pdf       | none                   | immediate_success |
      | success2.pdf       | none                   | immediate_success |
      | retry_success1.pdf | temporary_lock         | retry_success     |
      | retry_success2.pdf | network_timeout        | retry_success     |
      | retry_success3.pdf | permission_delay       | retry_success     |
      | permanent_fail1.pdf| corrupted_content      | permanent_failure |
      | permanent_fail2.pdf| unsupported_format     | permanent_failure |
      | success3.pdf       | none                   | immediate_success |
      | retry_success4.pdf | disk_space_delay       | retry_success     |
    When I run the document processing
    Then I should see clear visual and textual distinction between:
      | outcome_type           | count | display_treatment                    |
      | immediate_successes    | 3     | "✓ Success" with no retry indication |
      | retry_successes        | 4     | "✓ Success (retried)" clearly marked |
      | permanent_failures     | 2     | "✗ Failed" with error explanation    |
    And the progress counters should update accurately throughout processing
    And the final statistics should clearly show:
      | metric              | value | meaning                                    |
      | successful_files    | 7     | immediate successes + retry successes     |
      | failed_files        | 2     | only the permanently failed files         |
      | retry_attempts      | 4     | files that needed retries but succeeded   |
    And successful files (including retry successes) should be in processed directory
    And failed files should be in unprocessed directory with error explanations
    And I should understand the difference between temporary and permanent issues

  @workflow @user_confidence @e2e
  Scenario: User maintains confidence throughout retry process
    Given I have 4 files in the input directory
    And all 4 files will encounter temporary issues but eventually succeed
    When I run the document processing
    Then I should see encouraging messages throughout the retry process:
      | stage                    | message_tone                                      |
      | initial_failures         | "Temporary issues detected, retrying..."          |
      | retry_attempts           | "Retry 1 of 3 for file1.pdf..."                  |
      | partial_successes        | "2 of 4 files recovered successfully..."          |
      | final_success           | "All files processed successfully!"               |
    And I should never see discouraging language about "failures" for temporary issues
    And the progress display should maintain an optimistic but realistic tone
    And I should see clear indication that the system is actively working to resolve issues
    And when all files succeed, I should feel confident that the process worked correctly
    And I should trust the system to handle similar situations in the future
    And the final message should emphasize the successful outcome despite initial challenges

  @workflow @complex_retry_scenarios @e2e
  Scenario: Complex retry scenarios with multiple failure types resolve correctly
    Given I have 12 files with various temporary issues that will all eventually resolve:
      | files_count | issue_type           | retry_attempts_needed | resolution_time |
      | 3           | antivirus_scanning   | 1                     | 30 seconds      |
      | 2           | network_intermittent | 2                     | 45 seconds      |
      | 2           | disk_space_cleanup   | 1                     | 20 seconds      |
      | 3           | permission_elevation | 1                     | 15 seconds      |
      | 2           | none                | 0                     | immediate       |
    When I run the document processing
    Then I should see organized, clear communication about each issue type
    And different issue types should be handled with appropriate retry strategies
    And I should see progress updates that group similar issues together
    And the retry timing should be appropriate for each issue type
    And all 12 files should eventually process successfully
    And the final statistics should accurately reflect:
      | metric                    | expected_value                        |
      | total_successful          | 12                                   |
      | total_failed             | 0                                    |
      | total_retry_attempts     | 7 (3+2+2+3+2+0)                     |
      | average_processing_time   | reasonable given retry complexity    |
    And I should understand that complex retry scenarios are handled systematically
    And I should feel confident that the system robustly handles various temporary issues