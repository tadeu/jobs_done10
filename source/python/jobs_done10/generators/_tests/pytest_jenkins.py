from ben10.foundation.string import Dedent
from jobs_done10.generators.jenkins import JenkinsJobGenerator
from jobs_done10.job_generator import JobGeneratorConfigurator
from jobs_done10.jobs_done_file import JobsDoneFile
from jobs_done10.repository import Repository
import functools
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    #===============================================================================================
    # Setup for common results in all tests
    #===============================================================================================
    # Baseline expected XML. All tests are compared against this baseline, this way each test only
    # has to verify what is expected to be different, this way, if the baseline is changed, we don't
    # have to fix all tests.
    BASIC_EXPECTED_XML = Dedent(
        '''
        <?xml version="1.0" ?>
        <project>
          <actions/>
          <description>&lt;!-- Managed by Jenkins Job Builder --&gt;</description>
          <keepDependencies>false</keepDependencies>
          <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
          <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
          <concurrentBuild>false</concurrentBuild>
          <assignedNode>fake</assignedNode>
          <canRoam>false</canRoam>
          <logRotator>
            <daysToKeep>7</daysToKeep>
            <numToKeep>16</numToKeep>
            <artifactDaysToKeep>-1</artifactDaysToKeep>
            <artifactNumToKeep>-1</artifactNumToKeep></logRotator>
          <properties/>
          <scm class="hudson.plugins.git.GitSCM">
            <configVersion>2</configVersion>
            <userRemoteConfigs>
              <hudson.plugins.git.UserRemoteConfig>
                <name>origin</name>
                <refspec>+refs/heads/*:refs/remotes/origin/*</refspec>
                <url>http://fake.git</url>
              </hudson.plugins.git.UserRemoteConfig>
            </userRemoteConfigs>
            <branches>
              <hudson.plugins.git.BranchSpec>
                <name>master</name>
              </hudson.plugins.git.BranchSpec>
            </branches>
            <excludedUsers/>
            <buildChooser class="hudson.plugins.git.util.DefaultBuildChooser"/>
            <disableSubmodules>false</disableSubmodules>
            <recursiveSubmodules>false</recursiveSubmodules>
            <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
            <authorOrCommitter>false</authorOrCommitter>
            <clean>false</clean>
            <wipeOutWorkspace>false</wipeOutWorkspace>
            <pruneBranches>false</pruneBranches>
            <remotePoll>false</remotePoll>
            <gitTool>Default</gitTool>
            <submoduleCfg class="list"/>
            <relativeTargetDir>fake</relativeTargetDir>
            <reference/>
            <gitConfigName/>
            <gitConfigEmail/>
            <skipTag>false</skipTag>
            <scmName/>
          </scm>
          <builders/>
          <publishers/>
          <buildWrappers/>
        </project>
        ''',
        ignore_last_linebreak=False
    )


    def testEmpty(self):
        '''
        Tests the most basic YAML possible (created from no ci_contents at all)

        If this test fails, tests marked with @_SkipIfFailTestEmpty will be skipped.
        '''
        self._DoTest(ci_contents='', expected_diff='')


    def _SkipIfFailTestEmpty(original_test):  # @NoSelf
        '''
        Decorator that skips tests if self.testEmpty fails.

        This is useful because if a change is made to the most basic YAML possible (created from
        no ci_contents at all), all tests would fail, polluting the output.

        Fixing testEmpty should make other tests run again.
        '''
        @functools.wraps(original_test)
        def testFunc(self, *args, **kwargs):
            try:
                self.testEmpty()
            except:
                pytest.skip('Skipping until testEmpty is fixed.')
                return
            return original_test(self, *args, **kwargs)

        return testFunc


    #===============================================================================================
    # Tests
    #===============================================================================================
    @_SkipIfFailTestEmpty
    def testParameters(self):
        self._DoTest(
            ci_contents=Dedent(
                '''
                parameters:
                  - choice:
                      name: "PARAM"
                      choices:
                      - "choice_1"
                      - "choice_2"
                      description: "Description"
                '''
            ),
            expected_diff=Dedent(
                '''
                @@ @@
                -  <properties/>
                +  <properties>
                +    <hudson.model.ParametersDefinitionProperty>
                +      <parameterDefinitions>
                +        <hudson.model.ChoiceParameterDefinition>
                +          <name>PARAM</name>
                +          <description>Description</description>
                +          <choices class="java.util.Arrays$ArrayList">
                +            <a class="string-array">
                +              <string>choice_1</string>
                +              <string>choice_2</string>
                +            </a>
                +          </choices>
                +        </hudson.model.ChoiceParameterDefinition>
                +      </parameterDefinitions>
                +    </hudson.model.ParametersDefinitionProperty>
                +  </properties>
                '''
            ),
        )


    @_SkipIfFailTestEmpty
    def testJUnitPatterns(self):
        self._DoTest(
            ci_contents=Dedent(
                '''
                junit_patterns:
                - "junit*.xml"
                '''
            ),
            expected_diff=Dedent(
                '''
                @@ @@
                -  <publishers/>
                +  <publishers>
                +    <xunit>
                +      <types>
                +        <JUnitType>
                +          <pattern>junit*.xml</pattern>
                +          <skipNoTestFiles>true</skipNoTestFiles>
                +          <failIfNotNew>false</failIfNotNew>
                +          <deleteOutputFiles>true</deleteOutputFiles>
                +          <stopProcessingIfError>true</stopProcessingIfError>
                +        </JUnitType>
                +      </types>
                +      <thresholds>
                +        <org.jenkinsci.plugins.xunit.threshold.FailedThreshold>
                +          <unstableThreshold>0</unstableThreshold>
                +          <unstableNewThreshold>0</unstableNewThreshold>
                +        </org.jenkinsci.plugins.xunit.threshold.FailedThreshold>
                +      </thresholds>
                +      <thresholdMode>1</thresholdMode>
                +    </xunit>
                +  </publishers>
                '''
            ),

        )

    @_SkipIfFailTestEmpty
    def testMulitpleTestResults(self):
        self._DoTest(
            ci_contents=Dedent(
                '''
                junit_patterns:
                - "junit*.xml"

                boosttest_patterns:
                - "boosttest*.xml"
                '''
            ),
            expected_diff=Dedent(
                '''
                @@ @@
                -  <publishers/>
                +  <publishers>
                +    <xunit>
                +      <types>
                +        <JUnitType>
                +          <pattern>junit*.xml</pattern>
                +          <skipNoTestFiles>true</skipNoTestFiles>
                +          <failIfNotNew>false</failIfNotNew>
                +          <deleteOutputFiles>true</deleteOutputFiles>
                +          <stopProcessingIfError>true</stopProcessingIfError>
                +        </JUnitType>
                +        <BoostTestJunitHudsonTestType>
                +          <pattern>boosttest*.xml</pattern>
                +          <skipNoTestFiles>true</skipNoTestFiles>
                +          <failIfNotNew>false</failIfNotNew>
                +          <deleteOutputFiles>true</deleteOutputFiles>
                +          <stopProcessingIfError>true</stopProcessingIfError>
                +        </BoostTestJunitHudsonTestType>
                +      </types>
                +      <thresholds>
                +        <org.jenkinsci.plugins.xunit.threshold.FailedThreshold>
                +          <unstableThreshold>0</unstableThreshold>
                +          <unstableNewThreshold>0</unstableNewThreshold>
                +        </org.jenkinsci.plugins.xunit.threshold.FailedThreshold>
                +      </thresholds>
                +      <thresholdMode>1</thresholdMode>
                +    </xunit>
                +  </publishers>
                '''
            ),

        )


    @_SkipIfFailTestEmpty
    def testBuildBatchCommand(self):
        self._DoTest(
            ci_contents=Dedent(
                '''
                build_batch_command: my_command
                '''
            ),
            expected_diff=Dedent(
                '''
                @@ @@
                -  <builders/>
                +  <builders>
                +    <hudson.tasks.BatchFile>
                +      <command>my_command</command>
                +    </hudson.tasks.BatchFile>
                +  </builders>
                '''
            ),

        )

        self._DoTest(
            ci_contents=Dedent(
                '''
                build_batch_command: |
                  multi_line
                  command
                '''
            ),
            expected_diff=Dedent(
                '''
                @@ @@
                -  <builders/>
                +  <builders>
                +    <hudson.tasks.BatchFile>
                +      <command>multi_line
                +command</command>
                +    </hudson.tasks.BatchFile>
                +  </builders>
                '''
            ),

        )


    @_SkipIfFailTestEmpty
    def testDescriptionSetter(self):
        self._DoTest(
            ci_contents=Dedent(
                r'''
                description_regex: "JENKINS DESCRIPTION\\: (.*)"
                '''
            ),
            expected_diff=Dedent(
                r'''
                @@ @@
                -  <publishers/>
                +  <publishers>
                +    <hudson.plugins.descriptionsetter.DescriptionSetterPublisher>
                +      <regexp>JENKINS DESCRIPTION\: (.*)</regexp>
                +      <regexpForFailed>JENKINS DESCRIPTION\: (.*)</regexpForFailed>
                +      <setForMatrix>false</setForMatrix>
                +    </hudson.plugins.descriptionsetter.DescriptionSetterPublisher>
                +  </publishers>
                '''
            ),

        )


    @_SkipIfFailTestEmpty
    def testVariables(self):
        ci_contents = Dedent(
            '''
            planet:
            - earth
            - mars

            moon:
            - europa
            '''
        )
        repository = Repository(url='http://fake.git')

        # This test should create two jobs_done_files from their variations
        jobs_done_files = JobsDoneFile.CreateFromYAML(ci_contents)

        job_generator = JenkinsJobGenerator(repository)
        for jd_file in jobs_done_files:
            JobGeneratorConfigurator.Configure(job_generator, jd_file)
            jenkins_job = job_generator.GenerateJobs()

            planet = jd_file.variation['planet']
            self._AssertDiff(
                jenkins_job.xml,
                Dedent(
                    '''
                    @@ @@
                    -  <assignedNode>fake</assignedNode>
                    +  <assignedNode>fake-europa-%(planet)s</assignedNode>
                    ''' % locals()
                )
            )


    def _DoTest(self, ci_contents, expected_diff):
        '''
        :param str ci_contents:
            Contents of JobsDoneFile used for this test

        :param str expected_diff:
            Expected diff from build jobs from `ci_contents`, when compared to BASIC_EXPECTED_XML.
        '''
        repository = Repository(url='http://fake.git')
        jobs_done_files = JobsDoneFile.CreateFromYAML(ci_contents)

        job_generator = JenkinsJobGenerator(repository)
        JobGeneratorConfigurator.Configure(job_generator, jobs_done_files[0])
        jenkins_job = job_generator.GenerateJobs()

        self._AssertDiff(jenkins_job.xml, expected_diff)


    def _AssertDiff(self, obtained_yaml, expected_diff):
        import difflib

        diff = ''.join(difflib.unified_diff(
            self.BASIC_EXPECTED_XML.splitlines(1),
            str(obtained_yaml).splitlines(1),
            n=0,
        ))
        diff = '\n'.join(diff.splitlines()[2:])
        import re
        diff = re.sub('@@.*@@', '@@ @@', diff, flags=re.MULTILINE)

        print diff
        assert expected_diff == diff