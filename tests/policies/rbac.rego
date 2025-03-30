package app.rbac
import rego.v1
default allow := false
# Allow the action if the user is granted permission to perform the action.
allow if {
    # unless user location is outside US
    country := data.users[input.user].location.country
    country == "US"
}
