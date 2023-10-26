import unittest

from common.service_impl.learn_knowledge_index import retrieve_chunks_for_atomic_task


class TestRetrieveChunk(unittest.IsolatedAsyncioTestCase):
    async def test_retrieve_chunk(self):
        chunk = await retrieve_chunks_for_atomic_task('Install Service Mesh on the Cluster')
        self.assertIsNotNone(chunk)
