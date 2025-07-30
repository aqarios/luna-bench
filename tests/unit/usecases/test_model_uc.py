
from luna_bench import UsecaseContainer
from luna_bench._internal.usecases import ModelAllUc


class TestModelUc:

    
    def test_model_all(self, usecase: UsecaseContainer)-> None:
        uc:ModelAllUc = usecase.model_all_uc()
        assert len(uc())==2
        