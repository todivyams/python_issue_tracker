*** Settings ***
Library             RequestsLibrary
Library             Collections



*** Variables ***
${base_url}         http://localhost:5000/
${key}              token
${headerkey}        x-api-key



*** Test Cases ***
Sample Test 1
    [Tags]              Sample
    Log to console      hello, world.

Home page Test2
    [Tags]              Sample
    Create Session      home  http://localhost:5000/
    ${resp}=            GET On Session  home  /  expected_status=200


login Admin Test 3
    [Tags]              login
    ${usercredentials}=            Create list     admin1    passwd1
    Create Session      home  http://localhost:5000/        auth=${usercredentials}

    ${resp}=            POST On Session     home    /login      expected_status=200
    ${admintoken}=      get from dictionary         ${resp.json()}      ${key}
    Set global variable     ${admintoken}


List Users Test 4
    [Tags]              users
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}    ${admintoken}
    ${resp}=            GET On Session     home    /users    headers=${header}        expected_status=200
    Log to console      ${resp.json()}

No User Test 5
    [Tags]              users
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}    ${admintoken}
    ${resp}=            GET On Session     home    /users/5    headers=${header}        expected_status=404
    Log to console      ${resp.json()}

Register New User Test 6
    [Tags]              users
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${body}=            Create dictionary        User Name=user1   Password=passwd      Email=user1@email.com
    ${resp}=            POST On Session     home    /users    json=${body}     headers=${header}    expected_status=200
    Log to console      ${resp.json()}

Register New User Test 7
    [Tags]              users
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${body}=            Create dictionary        User Name=user2   Password=passwd      Email=user2@email.com
    ${resp}=            POST On Session     home    /users    json=${body}     headers=${header}    expected_status=200
    Log to console      ${resp.json()}

List Users Test 8
    [Tags]              users
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}    ${admintoken}
    ${resp}=            GET On Session     home    /users    headers=${header}        expected_status=200
    Log to console      ${resp.json()}

login User Test 9
    [Tags]              login
    ${usercredentials}=            Create list     user1    passwd
    Create Session      home  http://localhost:5000/        auth=${usercredentials}

    ${resp}=            POST On Session     home    /login      expected_status=200
    ${usertoken}=      get from dictionary         ${resp.json()}      ${key}
    Set global variable     ${usertoken}

Register User by User Test 10
    [Tags]              users
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${usertoken}
    ${body}=            Create dictionary        User Name=user2   Password=passwd      Email=user2@email.com
    ${resp}=            POST On Session     home    /users    json=${body}     headers=${header}    expected_status=401
    Log to console      ${resp.json()}

Create Bug Test 11
    [Tags]              bugs
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${body}=            Create dictionary        Bug Description=Description of bug1   Bug Title=bug1
    ${resp}=            POST On Session     home    /bugs    json=${body}     headers=${header}    expected_status=200
    Log to console      ${resp.json()}

Create Bug Test 12
    [Tags]              bugs
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${body}=            Create dictionary        Bug Description=Description of bug2   Bug Title=bug2
    ${resp}=            POST On Session     home    /bugs    json=${body}     headers=${header}    expected_status=200
    Log to console      ${resp.json()}


Assign Bug Test 13
    [Tags]              bugs
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${body}=            Create dictionary        Assigned To=user1
    ${resp}=            PUT On Session     home    /bugs/assign/1   json=${body}     headers=${header}    expected_status=200
    Log to console      ${resp.json()}

Change Bug Status Test 14
    [Tags]              bugs
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${body}=            Create dictionary        Status=Assigned
    ${resp}=            PUT On Session     home    /bugs/updatestatus/1   json=${body}     headers=${header}    expected_status=200
    Log to console      ${resp.json()}

Add Comment To A Bug Test 15
    [Tags]              bugs
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${body}=            Create dictionary        Comment=commented on bug 1
    ${resp}=            Post On Session     home    /bugs/addcomments/1   json=${body}     headers=${header}    expected_status=200
    Log to console      ${resp.json()}


Add Second Comments To A Bug Test 16
    [Tags]              bugs
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${usertoken}
    ${body}=            Create dictionary        Comment= second comment on bug 1
    ${resp}=            Post On Session     home    /bugs/addcomments/1   json=${body}     headers=${header}    expected_status=200
    Log to console      ${resp.json()}


Delete Bug Test 17
    [Tags]              bugs
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${resp}=            Delete On Session     home    /bugs/1      headers=${header}    expected_status=200
    Log to console      ${resp.json()}


Delete Bug Test 18
    [Tags]              bugs
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${resp}=            Delete On Session     home    /bugs/2      headers=${header}    expected_status=200
    Log to console      ${resp.json()}


Delete User Test 19
    [Tags]              users
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${resp}=            Delete On Session     home    /users/2    headers=${header}    expected_status=200
    Log to console      ${resp.json()}

Delete User Test 20
    [Tags]              users
    Create Session      home  http://localhost:5000
    ${header}=          Create dictionary        ${headerkey}=${admintoken}
    ${resp}=            Delete On Session     home    /users/3    headers=${header}    expected_status=200
    Log to console      ${resp.json()}


