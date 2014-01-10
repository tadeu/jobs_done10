# Name of jobs_done file, repositories must contain this file in their root dir to be able to
# create jobs.
import yaml
JOBS_DONE_FILENAME = '.jobs_done.yaml'



#===================================================================================================
# JobsDoneJob
#===================================================================================================
class JobsDoneJob(object):
    '''
    Represents a jobs_done job, parsed from a jobs_done file.

    This is a generic representation, not related to any specific continuous integration tool.
    '''

    # Options that should be forwarded to generators. These are set in JobsDoneJob instances
    # after parsing (setattr(option_name, self, value)), and are available as object fields
    GENERATOR_OPTIONS = {
        # list(str): Patterns to match when looking for boosttest results.
        'boosttest_patterns':list,

        # list(str): Shell script commands used to build a project.
        'build_shell_commands':list,

        # list(str): Batch script commands used to build a project.
        'build_batch_commands':list,

        # str: Regex pattern to be matched from a job output and used as job description. (Jenkins)
        'description_regex':str,

        # list(str): List of patterns to match when looking for junit test results.
        'junit_patterns':list,

        # Definition of parameters available to this job.
        # Uses jenkins-job-builder syntax parsed by yaml.
        # .. seealso:: http://ci.openstack.org/jenkins-job-builder/parameters.html
        #
        # e.g.
        #     parameters = {'choices' : ['1', '2'], 'name' : 'my_param'}
        'parameters':list,
    }

    # All parsed options
    PARSEABLE_OPTIONS = GENERATOR_OPTIONS.copy()
    PARSEABLE_OPTIONS.update({
        # list(str) branch_patterns:
        #    A list of regexes to matcvh against branch names.
        #    Jobs for a branch will only be created if any of this pattern matches that name.
        #    .. note:: Uses python `re` syntax.
        'branch_patterns':list,

        # dict matrix:
        #     A dict that represents all possible job combinations created from this file.
        #
        #     When a jobs_done file is parsed, it can contain variables that form a matrix. For each
        #     possible combination of these variables, a JobsDoneJob class is created. They can be used
        #     for things such as creating jobs for multiple platforms from a single JobsDoneJob.
        #
        #     For example, if our file describes this matrix:
        #         matrix:
        #           planet:
        #           - earth
        #           - mars
        #
        #           moon:
        #           - europa
        #           - ganymede
        #
        #     This file's `matrix` will be:
        #         {'planet' : ['earth', 'mars], 'moon' : ['europa', 'ganymede']}
        #
        #     This file's `matrix_row` will have one of these values (one for each JobsDoneJob created):
        #         {'planet' : 'earth', 'moon' : 'europa'}
        #         {'planet' : 'earth', 'moon' : 'ganymede'}
        #         {'planet' : 'mars', 'moon' : 'europa'}
        #         {'planet' : 'mars', 'moon' : 'ganymede'}
        'matrix':dict,
    })


    def __init__(self):
        '''
        :ivar dict matrix_row:
            A dict that represents a single row from this file's `matrix`.

            .. seealso:: `matrix`@PARSEABLE_OPTIONS
        '''
        self.matrix_row = None

        # Initialize known options with None
        for option_name in self.PARSEABLE_OPTIONS:
            setattr(self, option_name, None)


    @classmethod
    def CreateFromYAML(cls, yaml_contents, repository):
        '''
        Creates JobsDoneJob's from a jobs_done file in a repository.

        This method parses that file and returns as many jobs as necessary. This number may vary
        based on how big the job matrix is, and no jobs might be generated at all if the file is
        empty or the current repository branch does not match anything in `branch_patterns` defined
        in the file.

        Jobs parsed by this method can use a string replacement syntax in their contents, and
        those strings can be replaced by the current values in the matrix_row for that job, or a few
        special replacements available to all jobs:
        - name: Name of the repository for which we are creating jobs
        - branch: Name of the repository branch for which we are creating jobs

        :param str yaml_contents:
            Contents of a jobs_done file, in YAML format.

        :param Repository repository:
            Repository information for jobs created from `yaml_contents`

        :return list(JobsDoneJob):
            List of jobs created for parameters.

        .. seealso:: JobsDoneJob
            For known options accepted in yaml_contents

        Example:
            repository = Repository(url='http://space.git', branch='milky_way')
            yaml_contents =
                """
                junit_patterns:
                - "{planet}-{branch}.xml"

                matrix:
                    planet:
                    - earth
                    - mars
                """

            resulting JobsDoneJob's:
                JobsDoneJob(junit_patterns="earth-milky_way.xml", matrix_row={'planet': 'earth'}),
                JobsDoneJob(junit_patterns="mars-milky_way.xml", matrix_row={'planet': 'mars'}),

        .. seealso: pytest_jobs_done_job
            For other examples
        '''
        if yaml_contents is None:
            return []

        # Load yaml
        jd_data = yaml.load(yaml_contents, Loader=cls._JobsDoneYamlLoader) or {}

        # Search for unknown options and type errors
        for option_name, option_value in jd_data.iteritems():
            option_name = option_name.rsplit(':', 1)[-1]
            if option_name not in JobsDoneJob.PARSEABLE_OPTIONS:
                raise UnknownJobsDoneFileOption(option_name)

            obtained_type = type(option_value)
            expected_type = JobsDoneJob.PARSEABLE_OPTIONS[option_name]
            if obtained_type != expected_type:
                raise JobsDoneFileTypeError(option_name, obtained_type, expected_type)

        # Check if this branch is acceptable (matches anything in branch_patterns)
        import re
        branch_patterns = jd_data.get('branch_patterns', ['.*'])
        if not any([re.match(pattern, repository.branch) for pattern in branch_patterns]):
            return []

        # List combinations based on job matrix defined by file
        matrix = jd_data.get('matrix', {})

        # >>> Write up all matrix_rows from possible combinations of the job matrix
        # >>> Stolen from http://stackoverflow.com/a/3873734/1209622
        import itertools as it
        matrix_rows = [dict(zip(matrix, p)) for p in it.product(*(matrix[v] for v in matrix))]


        # Finally, create all jobs_done files (only known options remain in jd_data)
        def ConditionMatch(matrix_row, condition):
            variable_name, variable_value = condition.split('-')
            return matrix_row[variable_name] == variable_value

        jobs_done_jobs = []
        for matrix_row in matrix_rows:
            jobs_done_job = JobsDoneJob()
            jobs_done_jobs.append(jobs_done_job)

            jobs_done_job.repository = repository
            jobs_done_job.matrix_row = matrix_row.copy()

            if not jd_data:
                # Handling for empty jobs, they still are valid since we don't know what a builder
                # will do with them, maybe fill it with defaults
                continue

            # Re-read jd_data replacing all matrix variables with their values in the current
            # matrix_row and special replacement variables 'branch' and 'name', based on repository.
            format_dict = matrix_row.copy()
            format_dict.update({'branch':repository.branch, 'name':repository.name})
            jd_string = (yaml.dump(jd_data, default_flow_style=False)[:-1])
            formatted_jd_string = jd_string.format(**format_dict)
            jd_formatted_data = yaml.load(formatted_jd_string)

            for option_name, option_value in jd_formatted_data.iteritems():

                # Check for option conditions
                if ':' in option_name:
                    conditions = option_name.split(':')[:-1]
                    option_name = option_name.split(':')[-1]

                    # Skip this option if any condition is not met
                    if not all([ConditionMatch(matrix_row, condition) for condition in conditions]):
                        continue

                setattr(jobs_done_job, option_name, option_value)

        return jobs_done_jobs


    @classmethod
    def CreateFromFile(cls, filename, repository):
        '''
        :param str filename:
            Path to a jobs_done file

        :param repository:
            .. seealso:: CreateFromYAML
        '''
        from ben10.filesystem import GetFileContents
        return cls.CreateFromYAML(GetFileContents(filename), repository)


    class _JobsDoneYamlLoader(yaml.loader.BaseLoader):
        '''
        Custom loader that treats everything as ascii strings
        '''
        def construct_scalar(self, *args, **kwargs):
            value = yaml.loader.BaseLoader.construct_scalar(self, *args, **kwargs)
            return value.encode('ascii')


#===================================================================================================
# UnknownJobsDoneJobOption
#===================================================================================================
class UnknownJobsDoneFileOption(RuntimeError):
    '''
    Raised when parsing an unknown option.
    '''
    def __init__(self, option_name):
        self.option_name = option_name
        RuntimeError.__init__(
            self,
            'Received unknown option "%s".\n\nAvailable options are:\n%s' % \
            (option_name, '\n'.join('- ' + o for o in sorted(JobsDoneJob.PARSEABLE_OPTIONS)))
        )



#===================================================================================================
# JobsDoneFileTypeError
#===================================================================================================
class JobsDoneFileTypeError(TypeError):
    '''
    Raised when parsing an option with a bad type.
    '''
    def __init__(self, option_name, obtained_type, expected_type):
        self.option_name = option_name
        self.obtained_type = obtained_type
        self.expected_type = expected_type
        self.option_name = option_name

        TypeError.__init__(
            self,
            'On option "%s". Expected "%s" but got "%s".' % \
            (option_name, expected_type, obtained_type)
        )