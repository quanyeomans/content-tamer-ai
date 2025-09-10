Feature: Golden Path - Organization and Clustering Workflows
  As a user
  I want the system to intelligently organize my processed files
  So that I can find related documents easily

  Background:
    Given I have a clean working environment
    And the AI service is responding normally
    And organization features are enabled
    And I have proper permissions on all directories

  @golden_path @organization @e2e
  Scenario: Intelligent content-based organization succeeds
    Given I have 6 PDF files about different topics in the input directory:
      | filename           | content_topic        |
      | budget_report.pdf  | financial_planning   |
      | tax_forms.pdf      | financial_planning   |
      | meeting_notes.pdf  | project_management   |
      | project_plan.pdf   | project_management   |
      | recipe_book.pdf    | cooking              |
      | manual.pdf         | technical_docs       |
    When I run the document processing with organization enabled
    Then I should see "Analyzing content for organization..." in the progress display
    And all 6 files should process successfully
    And files should be organized into topic-based folders:
      | folder_name         | expected_files       |
      | financial_planning  | 2 files             |
      | project_management  | 2 files             |
      | cooking            | 1 file              |
      | technical_docs     | 1 file              |
    And each folder should contain only files with related content
    And I should see confirmation of the organization structure created
    And the folder names should be meaningful and user-friendly

  @golden_path @clustering @e2e
  Scenario: Document clustering creates logical groups
    Given I have 9 documents with mixed content types:
      | filename              | content_type    | topic           |
      | contract_jan.pdf      | legal          | contracts       |
      | contract_feb.pdf      | legal          | contracts       |
      | contract_mar.pdf      | legal          | contracts       |
      | invoice_001.pdf       | financial      | billing         |
      | invoice_002.pdf       | financial      | billing         |
      | manual_v1.pdf         | technical      | documentation   |
      | manual_v2.pdf         | technical      | documentation   |
      | proposal_a.pdf        | business       | proposals       |
      | proposal_b.pdf        | business       | proposals       |
    When I run the document processing with clustering enabled
    Then I should see "Clustering documents by similarity..." in the progress display
    And all 9 files should process successfully
    And documents should be clustered into logical groups:
      | cluster_name    | expected_count |
      | contracts       | 3 files        |
      | billing         | 2 files        |
      | documentation   | 2 files        |
      | proposals       | 2 files        |
    And similar documents should be grouped together accurately
    And cluster names should reflect the content themes
    And I should see a summary of the clustering results

  @golden_path @learning @e2e
  Scenario: Organization system learns from user preferences
    Given I have previously organized files in specific folder patterns
    And the system has learned my organization preferences
    And I have 4 new similar files to process
    When I run the document processing with learning enabled
    Then the system should recognize patterns from my previous organizations
    And new files should be placed in folders consistent with my preferences
    And I should see "Applying learned organization patterns..." in the progress display
    And all files should be organized according to my established patterns
    And the system should suggest the organization choices it made
    And I should have the option to confirm or adjust the organization

  @golden_path @mixed_organization @e2e
  Scenario: Processing with both organization and expert mode succeeds
    Given I have configured expert mode with custom settings
    And I have enabled both clustering and folder organization
    And I have 8 files with diverse content in the input directory
    When I run the document processing in expert mode with organization
    Then I should see my custom expert settings applied during processing
    And all files should process according to my expert configuration
    And organization should still work correctly with expert settings
    And files should be both renamed according to expert rules AND organized into folders
    And I should see confirmation of both expert processing and organization results
    And the final directory structure should reflect both customizations and intelligent organization