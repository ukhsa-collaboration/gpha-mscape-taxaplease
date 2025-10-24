# Pull request template for mSCAPE code

1. Choose the correct checklist for your pull request. This will be "Writing a new component"  
   if your code has not yet been reviewed and is the first PR to main. If the PR is to make  
   an update to an existing component, this will be "Updating an existing component".
2. Complete all actions in the relevant checklist and tick off as they are completed by putting
   an "x" inside the square brackets. 
3. Submit the completed pull request to a reviewer.

## Writing a new component
- [ ] I have read the SOP for creating or updating code to be integrated into mSCAPE
- [ ] The repository contains all required files as set out in the SOP
- [ ] The code base contains no CLIMB IDs or other sensitive information
- [ ] All functions involving calls to Onyx have appropriate error handling
- [ ] If writing to Onyx, the code includes a "dry run" option
- [ ] The code has passed linting checks in ruff with no errors raised*
- [ ] I have written unit tests for all functions
- [ ] I have successfully run the code and unit tests on synthscape

## Updating an existing component
- [ ] I have read the SOP for creating or updating code to be integrated into mSCAPE
- [ ] The updated code base contains no CLIMB IDs or other sensitive information
- [ ] Version number bumped in pyproject.toml
- [ ] Changes documented in the component CHANGELOG.md
- [ ] Documentation has been updated if required
- [ ] I have added or updated unit tests to cover the changes made
- [ ] New and existing unit tests have passed
- [ ] The updated code has passed linting checks in ruff with no errors raised*
- [ ] I have successfully run the code and unit tests on synthscape

* Any exceptions/skipped codes to be added with justification in the pull request description below

  ## Pull request description

  Please include a short description of the aim of the pull request and changes made. Highlight
  any particular areas of code you would like a reviewer to focus on during the review.
