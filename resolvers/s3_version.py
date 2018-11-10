from sceptre.resolvers import Resolver
from sceptre.resolvers.stack_output import StackOutput

class S3Version(Resolver):
    NAME = "s3_version"

    def __init__(self, *args, **kwargs):
        super(S3Version, self).__init__(*args, **kwargs)

    def determine_stack_output(self, arg: str):
        return StackOutput(argument=arg,
                                  connection_manager=self.connection_manager,
                                  environment_config=self.environment_config,
                                  stack_config=self.stack_config,
                                  ).resolve()

    def determine_bucket_name(self, arg: str):
        if '::' in arg:
            return self.determine_stack_output(arg)
        else:
            return arg

    def resolve(self):
        """
        Resolves the latest version of an object
        Usage: !s3_version stack_name::output_name/object_key
        :return:
        """
        if self.argument:
            s3_bucket, s3_key = self.argument.split("/", 1)
            s3_bucket = self.determine_bucket_name(s3_bucket)
            print(f"[{self.NAME}] S3 bucket/key parsed from the argument -> s3_bucket={s3_bucket}, s3_key={s3_key}")

        elif "sceptre_user_data" in self.stack_config:
            code = self.stack_config.get("sceptre_user_data").get("Code", {})
            s3_bucket, s3_key = [code.get("S3Bucket"), code.get("S3Key")]
            s3_bucket = self.determine_bucket_name(s3_bucket)
            print(f"[{self.NAME}] S3 bucket/key parsed from sceptre_user_data['Code'] -> s3_bucket={s3_bucket}, s3_key={s3_key}")
        else:
            raise Exception("S3 bucket/key could not be parsed nor from the argument, neither from sceptre_user_data['Code']")

        try:
            result = self.connection_manager.call(
                service="s3",
                command="head_object",
                kwargs={"Bucket": s3_bucket, "Key": s3_key},
            )
            version_id = result.get("VersionId")
            print("[{}] object s3://{}/{} latest version: {}".format(self.NAME, s3_bucket, s3_key, version_id))
            return version_id
        except Exception as e:
            print(e)
            return ''
