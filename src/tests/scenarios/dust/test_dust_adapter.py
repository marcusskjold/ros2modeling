import roserer.yamlParser as yparser
import roserer.systemvalidator as sv
import pytest as pt
# import roserer.adapters.dust_adapter as da
import roserer.dust.dust_system as ds

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_transform_system_no_duplicate_subscribers() -> None:
    """
    Tests that a callback- and topic-template is made for each publisher to the same topic,
    but only 1 subscription-callback for each subscription to a topic is made.
    # TODO: also check no duplicate topics when same publisher!!!
    Even when same publisher used twice in two different callbacks.
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_transform_system_no_duplicate_subscribers.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert errors == []
    assert warnings == []
    assert len(dust_sys.topics) == 2
    assert len(dust_sys.callbacks) == 3

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_transform_system_detects_two_clients_same_service() -> None:
    """
    Tests service invoked from different clients isn't accepted by validator
    """ 
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_transform_system_detects_two_clients_same_service.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert "The same service is being requested from multiple sources. This model only support a service being requested from one place." in errors

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_transform_system_detects_one_client_different_responses() -> None:
    """
    Tests that two requests with same client but different response-callbacks
    are not accepted by the dust-validator
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_transform_system_detects_one_client_different_responses.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert errors != [] #TODO: specify message when merged with new validations

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_transform_system_no_duplicate_clients() -> None: ##TODO: implement
    """
    Tests that node calling same client from more callbacks doesn't result in duplicate templates
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_transform_system_no_duplicate_clients.yaml")

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_transform_system_service_client_correct_mapping() -> None:
    """
    Tests that a system simple system with service-client is mapped correctly
    (topic back and forth between server-client)
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_transform_system_service_client_correct_mapping.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert errors == []
    assert warnings == []
    assert len(dust_sys.executors) == 2
    assert len(dust_sys.topics) == 2
    assert len(dust_sys.callbacks) == 3
    expected_request_cb = ds.PeriodicCallback(id=0,exec_time=3, period=5, type=0, offset=0, buffersize=1,amount_of_publishers=1,publisher_release_time=[3], publisher_id=[0], executorID=0)
    expected_service_cb = ds.DataCallback(id=0, exec_time=7, topicID=0, type=1, buffersize=10,amount_of_publishers=1,publisher_release_time=[5], publisher_id=[1], executorID=1)
    expected_client_cb = ds.DataCallback(id=0,exec_time=1, topicID=1, type=3, buffersize=10,amount_of_publishers=0,publisher_release_time=[], publisher_id=[], executorID=0)
    expected_topic_1 = ds.Topic(receiver_id=0, sender_id=0, delay=0, max_jitter=0, buffersize=10)
    expected_topic_2 = ds.Topic(receiver_id=1, sender_id=1, delay=0, max_jitter=0, buffersize=10)
    component_attributes = [com.__dict__ for com in dust_sys.callbacks + dust_sys.topics]
    assert expected_service_cb.__dict__ in component_attributes
    assert expected_client_cb.__dict__ in component_attributes
    assert expected_request_cb.__dict__ in component_attributes
    assert expected_topic_1.__dict__ in component_attributes
    assert expected_topic_2.__dict__ in component_attributes

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_transform_system_nested_calls_collapsed() -> None:
    """
    Tests that a callback with nested calls is collapsed into a single callback
    with wcet = the sum of the callbacks and correct arrays for sending.
    Also checks that a separate topic is made for each publisher to same topic
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_transform_system_nested_calls_collapsed.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert errors == []
    assert warnings == []
    expected_components = []
    expected_components.append(ds.PeriodicCallback(id=0, exec_time=12, period=20, type=0, offset=0, buffersize=1, amount_of_publishers=3, publisher_release_time=[3,7,12], publisher_id=[0,1,2], executorID=0).__dict__)
    expected_components.append(ds.Topic(receiver_id=0, sender_id=0, delay=0,max_jitter=0,buffersize=10).__dict__)
    expected_components.append(ds.Topic(receiver_id=1, sender_id=1, delay=0,max_jitter=0,buffersize=10).__dict__)
    expected_components.append(ds.Topic(receiver_id=0, sender_id=2, delay=0,max_jitter=0,buffersize=10).__dict__)
    expected_components.append(ds.PeriodicCallback(id=1, exec_time=9, period=10, type=0, offset=0,buffersize=1,amount_of_publishers=2,publisher_release_time=[4,9],publisher_id=[1,2],executorID=0).__dict__) 
    expected_components.append(ds.DataCallback(id=0,exec_time=5,topicID=0,type=2,buffersize=10,amount_of_publishers=0,publisher_release_time=[],publisher_id=[],executorID=1).__dict__)
    expected_components.append(ds.DataCallback(id=1,exec_time=5,topicID=1,type=2,buffersize=10,amount_of_publishers=0,publisher_release_time=[],publisher_id=[],executorID=1).__dict__)
    expected_components.append(ds.DataCallback(id=2,exec_time=5,topicID=1,type=2,buffersize=10,amount_of_publishers=0,publisher_release_time=[],publisher_id=[],executorID=1).__dict__)
    component_attributes = [com.__dict__ for com in dust_sys.callbacks + dust_sys.topics]
    for com in expected_components:
        assert com in component_attributes
    assert len(component_attributes) == len(expected_components)

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_transform_system_cbs_correct_ids() -> None:
    """
    Tests that each callback is assigned correct id's
    -> id's should be assigned on a per callback-type per executor basis
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_transform_system_cbs_correct_ids.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert errors == []
    assert warnings == []
    timer_cb_ids = [cb.id for cb in dust_sys.callbacks if cb.type == 'TIMER']
    service_cb_ids = [cb.id for cb in dust_sys.callbacks if cb.type == 'SERVICE']
    subscription_cb_ids = [cb.id for cb in dust_sys.callbacks if cb.type == 'SUBSCRIBER']
    client_cb_ids = [cb.id for cb in dust_sys.callbacks if cb.type == 'CLIENT']
    assert timer_cb_ids == [0,1,0]
    assert service_cb_ids == [0,1]
    assert subscription_cb_ids == [0,1]
    assert client_cb_ids == [0,1]


@pt.mark.skip("Wait till Dust mapping has been completed")
def test_validate_timer_invalid_wcet_sum_caught() -> None:
    """
    Tests that a net sum wcet of a callback above the period of its timer
    is caught (when individual wcet of calls is below)
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_validate_timer_invalid_wcet_sum_caught.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert errors != []

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_validate_timer_edge_wcet_sum_accepted() -> None:
    """
    Tests that a net sum wcet of a callback equal to period of timer is accepted
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_validate_timer_edge_wcet_sum_accepted.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert errors == []

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_validate_system_disconnected_executors_detected() -> None:
    """
    Tests that a system with some executors not being connected prompts a warning.
    Uses system with 4 executors only connected in pairs
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_validate_system_disconnected_executors_detected.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert warnings != []

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_validate_system_disconnected_nodes_accepted() -> None:
    """
    Tests that system with two disconnected nodes under same executor is accepted
    """
    test_sys = yparser.parse_yaml("src/tests/input/dust/test_validate_system_disconnected_nodes_accepted.yaml")
    errors, warnings, dust_sys = da.transform_system(test_sys)
    assert len(warnings) == 2 # TODO: check for specific message not in there, when new validations loaded
    assert errors == []

@pt.mark.skip("Wait till Dust mapping has been completed")
def test_transform_system_callback_order_maintained() -> None:
    """
    Tests that the id's of callbacks reflects the order they were added
    to the node (required for correctly prioritizing callbacks of same type)
    """
