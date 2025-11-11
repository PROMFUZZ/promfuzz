library FuzzLand {
    event AssertionFailed(string message);

    function bug() internal {
        emit AssertionFailed("Bug");
    }

    function typed_bug(string memory data) internal {
        emit AssertionFailed(data);
    }

}