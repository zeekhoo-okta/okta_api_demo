variable "org_name" {}
variable "api_token" {}
variable "base_url" {}
variable "demo_app_name" {}
variable "udp_subdomain" {}

provider "okta" {
  org_name  = "${var.org_name}"
  api_token = "${var.api_token}"
  base_url  = "${var.base_url}"
  version   = "~> 3.0"
}
provider "local" {
  version = "~> 1.2"
}
data "okta_group" "all" {
  name = "Everyone"
}
resource "okta_app_oauth" "superDemoApp" {
  label          = "Super Widget Demo (Generated by UDP)"
  type           = "web"
  grant_types    = ["authorization_code", "implicit", "refresh_token"]
  redirect_uris  = ["https://${var.udp_subdomain}.${var.demo_app_name}.unidemo.online/oauth2/callback"]
  response_types = ["code", "token", "id_token"]
  groups         = ["${data.okta_group.all.id}"]
  consent_method = "TRUSTED"
}
resource "okta_app_bookmark" "loginDiscoBookmark" {
  label  = "LoginDisco_${okta_app_oauth.superDemoApp.client_id}"
  url    = "https://${var.udp_subdomain}.${var.demo_app_name}.unidemo.online/login-noprompt?from=login_idp_disco"
  groups = ["${data.okta_group.all.id}"]
}
resource "okta_auth_server" "superUnidemo" {
  audiences   = ["api://super.unidemo"]
  description = "super widget auth server"
  name        = "super.unidemo"
}
resource "okta_auth_server_claim" "resourceGroupsClaimR" {
  name              = "groups"
  status            = "ACTIVE"
  claim_type        = "RESOURCE"
  value_type        = "GROUPS"
  group_filter_type = "REGEX"
  value             = ".*"
  auth_server_id    = "${okta_auth_server.superUnidemo.id}"
}
resource "okta_auth_server_claim" "identityGroupsClaim" {
  name              = "groups"
  status            = "ACTIVE"
  claim_type        = "IDENTITY"
  value_type        = "GROUPS"
  group_filter_type = "REGEX"
  value             = ".*"
  auth_server_id    = "${okta_auth_server.superUnidemo.id}"
}
resource "okta_auth_server_policy" "superUnidemoDefaultPolicy" {
  status           = "ACTIVE"
  name             = "Default"
  description      = "Default"
  priority         = 1
  client_whitelist = ["ALL_CLIENTS"]
  auth_server_id   = "${okta_auth_server.superUnidemo.id}"
}
resource "okta_auth_server_policy_rule" "superUnidemoDefaultPolicyRule" {
  auth_server_id       = "${okta_auth_server.superUnidemo.id}"
  policy_id            = "${okta_auth_server_policy.superUnidemoDefaultPolicy.id}"
  status               = "ACTIVE"
  name                 = "Default"
  priority             = 1
  group_whitelist      = ["EVERYONE"]
  grant_type_whitelist = ["authorization_code", "implicit", "client_credentials"]
  scope_whitelist      = ["*"]
}
resource "okta_trusted_origin" "superUnidemo" {
  name   = "${var.udp_subdomain}.${var.demo_app_name}.unidemo.online"
  origin = "https://${var.udp_subdomain}.${var.demo_app_name}.unidemo.online"
  scopes = ["CORS"]
}

output "client_id" {
  value = "${okta_app_oauth.superDemoApp.client_id}"
}
output "client_secret" {
  value = "${okta_app_oauth.superDemoApp.client_secret}"
}
output "issuer" {
  value = "${okta_auth_server.superUnidemo.issuer}"
}