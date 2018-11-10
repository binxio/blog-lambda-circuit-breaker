from sceptre.hooks import Hook
from sceptre.resolvers.stack_output import StackOutput
from collections import defaultdict


class S3EmptyBucket(Hook):
    NAME = 's3_empty_bucket'
    def __init__(self, *args, **kwargs):
        super(S3EmptyBucket, self).__init__(*args, **kwargs)

    id_list = defaultdict()
    del_obj_list = defaultdict(list)

    def run(self):
        """
        Removes all objects from a bucket
        Usage: !s3_empty_bucket stack_name::output_name
        :return:
        """
        try:
            bucket_name = StackOutput(argument=self.argument,
                                      connection_manager=self.connection_manager,
                                      environment_config=self.environment_config,
                                      stack_config=self.stack_config,
                                      ).resolve()

            print(f"[{self.NAME}] Emptying bucket: {bucket_name}")
            s3 = self.connection_manager.boto_session.resource('s3')
            bucket = s3.Bucket(bucket_name)
            s3_client = self.connection_manager.boto_session.client('s3')
            resp = s3_client.list_object_versions(Bucket=bucket_name)

            del_markers = {}
            # All delete markers that are latest version, i.e., should be deleted
            if resp.get('DeleteMarkers'):
                del_markers = {item['Key']: item['VersionId'] for item in resp['DeleteMarkers'] if item['IsLatest'] == True}

            # all objects must be deleted
            for item in resp['Versions']:
                self.del_obj_list[item['Key']].append(item['VersionId'])

            # Remove old versions of object by VersionId
            for del_item in self.del_obj_list:
                print(f'[{self.NAME}] Deleting: {del_item}')
                rm_obj = bucket.Object(del_item)

                for del_id in self.del_obj_list[del_item]:
                    rm_obj.delete(VersionId=del_id)

                # Remove delete marker
                rm_obj.delete(VersionId=del_markers[del_item])

            bucket.objects.all().delete()
        except Exception as e:
            print(f'[{self.NAME}] Error: {e}')
