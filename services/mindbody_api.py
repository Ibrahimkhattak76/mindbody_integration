# -*- coding: utf-8 -*-
import logging
import time
from datetime import timedelta

import requests

from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyAPI(models.AbstractModel):
    _name = "mindbody.api"
    _description = "Mindbody Public API v6 Service"

    BASE_URL = "https://api.mindbodyonline.com/public/v6"

    # ----------------------------
    # Mindbody v6 Endpoints
    # ----------------------------
    ENDPOINTS = {
        "delete_appointment_appointmentfromwaitlist": {'method': 'DELETE',
                                                       'path': '/appointment/appointmentfromwaitlist'},
        "delete_appointment_availability": {'method': 'DELETE', 'path': '/appointment/availability'},
        "delete_appointment_deleteappointmentaddon": {'method': 'DELETE',
                                                      'path': '/appointment/deleteappointmentaddon'},
        "delete_client_clientdirectdebitinfo": {'method': 'DELETE', 'path': '/client/clientdirectdebitinfo'},
        "delete_client_clientformulanote": {'method': 'DELETE', 'path': '/client/clientformulanote'},
        "delete_client_deletecontactlog": {'method': 'DELETE', 'path': '/client/deletecontactlog'},
        "delete_pickaspot_reservation_by_pathinfo": {'method': 'DELETE', 'path': '/pickaspot/v1/reservation/{pathInfo}',
                                                     'result_key': 'Headers'},
        "get_appointment_activesessiontimes": {'method': 'GET', 'path': '/appointment/activesessiontimes',
                                               'result_key': 'ActiveSessionTimes'},
        "get_appointment_addons": {'method': 'GET', 'path': '/appointment/addons', 'result_key': 'AddOns'},
        "get_appointment_appointmentoptions": {'method': 'GET', 'path': '/appointment/appointmentoptions',
                                               'result_key': 'Options'},
        "get_appointment_availabledates": {'method': 'GET', 'path': '/appointment/availabledates',
                                           'result_key': 'AvailableDates'},
        "get_appointment_bookableitems": {'method': 'GET', 'path': '/appointment/bookableitems',
                                          'result_key': 'Availabilities'},
        "get_appointment_scheduleitems": {'method': 'GET', 'path': '/appointment/scheduleitems',
                                          'result_key': 'StaffMembers'},
        "get_appointment_staffappointments": {'method': 'GET', 'path': '/appointment/staffappointments',
                                              'result_key': 'Appointments'},
        "get_appointment_unavailabilities": {'method': 'GET', 'path': '/appointment/unavailabilities',
                                             'result_key': 'Unavailabilities'},
        "get_class_classdescriptions": {'method': 'GET', 'path': '/class/classdescriptions',
                                        'result_key': 'ClassDescriptions'},
        "get_class_classes": {'method': 'GET', 'path': '/class/classes', 'result_key': 'Classes'},
        "get_class_classschedules": {'method': 'GET', 'path': '/class/classschedules'},
        "get_class_classvisits": {'method': 'GET', 'path': '/class/classvisits', 'result_key': 'Class'},
        "get_class_courses": {'method': 'GET', 'path': '/class/courses', 'result_key': 'Courses'},
        "get_class_semesters": {'method': 'GET', 'path': '/class/semesters', 'result_key': 'Semesters'},
        "get_class_waitlistentries": {'method': 'GET', 'path': '/class/waitlistentries'},
        "get_client_activeclientmemberships": {'method': 'GET', 'path': '/client/activeclientmemberships',
                                               'result_key': 'ClientMemberships'},
        "get_client_activeclientsmemberships": {'method': 'GET', 'path': '/client/activeclientsmemberships',
                                                'result_key': 'ClientMemberships'},
        "get_client_clientaccountbalances": {'method': 'GET', 'path': '/client/clientaccountbalances',
                                             'result_key': 'Clients'},
        "get_client_clientcompleteinfo": {'method': 'GET', 'path': '/client/clientcompleteinfo',
                                          'result_key': 'Client'},
        "get_client_clientcontracts": {'method': 'GET', 'path': '/client/clientcontracts', 'result_key': 'Contracts'},
        "get_client_clientdirectdebitinfo": {'method': 'GET', 'path': '/client/clientdirectdebitinfo',
                                             'result_key': 'NameOnAccount'},
        "get_client_clientduplicates": {'method': 'GET', 'path': '/client/clientduplicates',
                                        'result_key': 'ClientDuplicates'},
        "get_client_clientformulanotes": {'method': 'GET', 'path': '/client/clientformulanotes',
                                          'result_key': 'FormulaNotes'},
        "get_client_clientindexes": {'method': 'GET', 'path': '/client/clientindexes', 'result_key': 'ClientIndexes'},
        "get_client_clientpurchases": {'method': 'GET', 'path': '/client/clientpurchases', 'result_key': 'Purchases'},
        "get_client_clientreferraltypes": {'method': 'GET', 'path': '/client/clientreferraltypes',
                                           'result_key': 'ReferralTypes'},
        "get_client_clientrewards": {'method': 'GET', 'path': '/client/clientrewards', 'result_key': 'Balance'},
        "get_client_clients": {'method': 'GET', 'path': '/client/clients', 'result_key': 'Clients'},
        "get_client_clientschedule": {'method': 'GET', 'path': '/client/clientschedule', 'result_key': 'Visits'},
        "get_client_clientservices": {'method': 'GET', 'path': '/client/clientservices',
                                      'result_key': 'ClientServices'},
        "get_client_clientvisits": {'method': 'GET', 'path': '/client/clientvisits', 'result_key': 'Visits'},
        "get_client_contactlogs": {'method': 'GET', 'path': '/client/contactlogs', 'result_key': 'ContactLogs'},
        "get_client_contactlogtypes": {'method': 'GET', 'path': '/client/contactlogtypes',
                                       'result_key': 'ContactLogTypes'},
        "get_client_crossregionalclientassociations": {'method': 'GET',
                                                       'path': '/client/crossregionalclientassociations',
                                                       'result_key': 'CrossRegionalClientAssociations'},
        "get_client_customclientfields": {'method': 'GET', 'path': '/client/customclientfields',
                                          'result_key': 'CustomClientFields'},
        "get_client_requiredclientfields": {'method': 'GET', 'path': '/client/requiredclientfields',
                                            'result_key': 'RequiredClientFields'},
        "get_enrollment_enrollments": {'method': 'GET', 'path': '/enrollment/enrollments'},
        "get_pickaspot_class": {'method': 'GET', 'path': '/pickaspot/v1/class', 'result_key': 'classes'},
        "get_pickaspot_class_by_classid": {'method': 'GET', 'path': '/pickaspot/v1/class/{classId}',
                                           'result_key': 'classes'},
        "get_pickaspot_reservation_by_pathinfo": {'method': 'GET', 'path': '/pickaspot/v1/reservation/{pathInfo}',
                                                  'result_key': 'Reservations'},
        "get_sale_acceptedcardtypes": {'method': 'GET', 'path': '/sale/acceptedcardtypes'},
        "get_sale_alternativepaymentmethods": {'method': 'GET', 'path': '/sale/alternativepaymentmethods',
                                               'result_key': 'PaymentMethods'},
        "get_sale_contracts": {'method': 'GET', 'path': '/sale/contracts', 'result_key': 'Contracts'},
        "get_sale_custompaymentmethods": {'method': 'GET', 'path': '/sale/custompaymentmethods',
                                          'result_key': 'PaymentMethods'},
        "get_sale_giftcardbalance": {'method': 'GET', 'path': '/sale/giftcardbalance', 'result_key': 'BarcodeId'},
        "get_sale_giftcards": {'method': 'GET', 'path': '/sale/giftcards', 'result_key': 'GiftCards'},
        "get_sale_packages": {'method': 'GET', 'path': '/sale/packages', 'result_key': 'Packages'},
        "get_sale_products": {'method': 'GET', 'path': '/sale/products', 'result_key': 'Products'},
        "get_sale_productsinventory": {'method': 'GET', 'path': '/sale/productsinventory',
                                       'result_key': 'ProductsInventory'},
        "get_sale_purchasecontractstatus": {'method': 'GET', 'path': '/sale/purchasecontractstatus',
                                            'result_key': 'ClientId'},
        "get_sale_sales": {'method': 'GET', 'path': '/sale/sales', 'result_key': 'Sales'},
        "get_sale_services": {'method': 'GET', 'path': '/sale/services', 'result_key': 'Services'},
        "get_sale_transactions": {'method': 'GET', 'path': '/sale/transactions', 'result_key': 'Transactions'},
        "get_site_activationcode": {'method': 'GET', 'path': '/site/activationcode', 'result_key': 'ActivationCode'},
        "get_site_categories": {'method': 'GET', 'path': '/site/categories', 'result_key': 'Categories'},
        "get_site_genders": {'method': 'GET', 'path': '/site/genders', 'result_key': 'GenderOptions'},
        "get_site_liabilitywaiver": {'method': 'GET', 'path': '/site/liabilitywaiver', 'result_key': 'LiabilityWaiver'},
        "get_site_locations": {'method': 'GET', 'path': '/site/locations', 'result_key': 'Locations'},
        "get_site_memberships": {'method': 'GET', 'path': '/site/memberships', 'result_key': 'Memberships'},
        "get_site_mobileproviders": {'method': 'GET', 'path': '/site/mobileproviders', 'result_key': 'MobileProviders'},
        "get_site_paymenttypes": {'method': 'GET', 'path': '/site/paymenttypes', 'result_key': 'PaymentTypes'},
        "get_site_programs": {'method': 'GET', 'path': '/site/programs', 'result_key': 'Programs'},
        "get_site_promocodes": {'method': 'GET', 'path': '/site/promocodes', 'result_key': 'PromoCodes'},
        "get_site_prospectstages": {'method': 'GET', 'path': '/site/prospectstages', 'result_key': 'ProspectStages'},
        "get_site_relationships": {'method': 'GET', 'path': '/site/relationships', 'result_key': 'Relationships'},
        "get_site_resourceavailabilities": {'method': 'GET', 'path': '/site/resourceavailabilities',
                                            'result_key': 'ResourceAvailabilities'},
        "get_site_resources": {'method': 'GET', 'path': '/site/resources'},
        "get_site_sessiontypes": {'method': 'GET', 'path': '/site/sessiontypes', 'result_key': 'SessionTypes'},
        "get_site_sites": {'method': 'GET', 'path': '/site/sites', 'result_key': 'Sites'},
        "get_staff_salesreps": {'method': 'GET', 'path': '/staff/salesreps', 'result_key': 'SalesReps'},
        "get_staff_sessiontypes": {'method': 'GET', 'path': '/staff/sessiontypes', 'result_key': 'StaffSessionTypes'},
        "get_staff_staff": {'method': 'GET', 'path': '/staff/staff', 'result_key': 'StaffMembers'},
        "get_staff_staffpermissions": {'method': 'GET', 'path': '/staff/staffpermissions', 'result_key': 'UserGroup'},
        "patch_class_updateclassschedulenotes_by_classscheduleid": {'method': 'PATCH',
                                                                    'path': '/class/updateclassschedulenotes/{classScheduleId}',
                                                                    'result_key': 'Notes'},
        "post_appointment_addappointment": {'method': 'POST', 'path': '/appointment/addappointment',
                                            'result_key': 'Appointment'},
        "post_appointment_addappointmentaddon": {'method': 'POST', 'path': '/appointment/addappointmentaddon',
                                                 'result_key': 'AppointmentId'},
        "post_appointment_addmultipleappointments": {'method': 'POST', 'path': '/appointment/addmultipleappointments',
                                                     'result_key': 'AddAppointmentOutcomes'},
        "post_appointment_availabilities": {'method': 'POST', 'path': '/appointment/availabilities',
                                            'result_key': 'StaffMembers'},
        "post_appointment_updateappointment": {'method': 'POST', 'path': '/appointment/updateappointment',
                                               'result_key': 'Appointment'},
        "post_class_addclassschedule": {'method': 'POST', 'path': '/class/addclassschedule', 'result_key': 'ClassId'},
        "post_class_addclienttoclass": {'method': 'POST', 'path': '/class/addclienttoclass', 'result_key': 'Visit'},
        "post_class_cancelsingleclass": {'method': 'POST', 'path': '/class/cancelsingleclass', 'result_key': 'Class'},
        "post_class_removeclientfromclass": {'method': 'POST', 'path': '/class/removeclientfromclass',
                                             'result_key': 'Class'},
        "post_class_removeclientsfromclasses": {'method': 'POST', 'path': '/class/removeclientsfromclasses',
                                                'result_key': 'Classes'},
        "post_class_removefromwaitlist": {'method': 'POST', 'path': '/class/removefromwaitlist'},
        "post_class_substituteclassteacher": {'method': 'POST', 'path': '/class/substituteclassteacher',
                                              'result_key': 'Class'},
        "post_class_updateclass": {'method': 'POST', 'path': '/class/updateclass'},
        "post_class_updateclassschedule": {'method': 'POST', 'path': '/class/updateclassschedule',
                                           'result_key': 'ClassId'},
        "post_client_addarrival": {'method': 'POST', 'path': '/client/addarrival', 'result_key': 'ArrivalAdded'},
        "post_client_addclient": {'method': 'POST', 'path': '/client/addclient', 'result_key': 'Client'},
        "post_client_addclientdirectdebitinfo": {'method': 'POST', 'path': '/client/addclientdirectdebitinfo',
                                                 'result_key': 'ClientId'},
        "post_client_addclientformulanote": {'method': 'POST', 'path': '/client/addclientformulanote',
                                             'result_key': 'Id'},
        "post_client_addcontactlog": {'method': 'POST', 'path': '/client/addcontactlog', 'result_key': 'Id'},
        "post_client_clientrewards": {'method': 'POST', 'path': '/client/clientrewards', 'result_key': 'Balance'},
        "post_client_mergeclients": {'method': 'POST', 'path': '/client/mergeclients'},
        "post_client_sendautoemail": {'method': 'POST', 'path': '/client/sendautoemail'},
        "post_client_sendpasswordresetemail": {'method': 'POST', 'path': '/client/sendpasswordresetemail'},
        "post_client_suspendcontract": {'method': 'POST', 'path': '/client/suspendcontract', 'result_key': 'Contract'},
        "post_client_terminatecontract": {'method': 'POST', 'path': '/client/terminatecontract',
                                          'result_key': 'Contract'},
        "post_client_updateclient": {'method': 'POST', 'path': '/client/updateclient', 'result_key': 'Client'},
        "post_client_updateclientcontractautopays": {'method': 'POST', 'path': '/client/updateclientcontractautopays',
                                                     'result_key': 'Id'},
        "post_client_updateclientservice": {'method': 'POST', 'path': '/client/updateclientservice',
                                            'result_key': 'ClientService'},
        "post_client_updateclientvisit": {'method': 'POST', 'path': '/client/updateclientvisit', 'result_key': 'Visit'},
        "post_client_updatecontactlog": {'method': 'POST', 'path': '/client/updatecontactlog', 'result_key': 'Id'},
        "post_client_uploadclientdocument": {'method': 'POST', 'path': '/client/uploadclientdocument',
                                             'result_key': 'FileSize'},
        "post_client_uploadclientphoto": {'method': 'POST', 'path': '/client/uploadclientphoto',
                                          'result_key': 'ClientId'},
        "post_enrollment_addclienttoenrollment": {'method': 'POST', 'path': '/enrollment/addclienttoenrollment',
                                                  'result_key': 'Classes'},
        "post_enrollment_addenrollmentschedule": {'method': 'POST', 'path': '/enrollment/addenrollmentschedule',
                                                  'result_key': 'ClassId'},
        "post_enrollment_updateenrollmentschedule": {'method': 'POST', 'path': '/enrollment/updateenrollmentschedule',
                                                     'result_key': 'ClassId'},
        "post_pickaspot_reservation_by_pathinfo": {'method': 'POST', 'path': '/pickaspot/v1/reservation/{pathInfo}',
                                                   'result_key': 'Reservation'},
        "post_sale_checkoutshoppingcart": {'method': 'POST', 'path': '/sale/checkoutshoppingcart'},
        "post_sale_completecheckoutshoppingcart": {'method': 'POST', 'path': '/sale/completecheckoutshoppingcart'},
        "post_sale_initiatecheckoutshoppingcart": {'method': 'POST', 'path': '/sale/initiatecheckoutshoppingcart'},
        "post_sale_initiatepurchasecontract": {'method': 'POST', 'path': '/sale/initiatepurchasecontract'},
        "post_sale_purchaseaccountcredit": {'method': 'POST', 'path': '/sale/purchaseaccountcredit',
                                            'result_key': 'AmountPaid'},
        "post_sale_purchasecontract": {'method': 'POST', 'path': '/sale/purchasecontract', 'result_key': 'ClientId'},
        "post_sale_purchasegiftcard": {'method': 'POST', 'path': '/sale/purchasegiftcard', 'result_key': 'BarcodeId'},
        "post_sale_returnsale": {'method': 'POST', 'path': '/sale/returnsale', 'result_key': 'ReturnSaleID'},
        "post_sale_updateproductprice": {'method': 'POST', 'path': '/sale/updateproductprice', 'result_key': 'Product'},
        "post_site_addclientindex": {'method': 'POST', 'path': '/site/addclientindex', 'result_key': 'ClientIndexID'},
        "post_site_addpromocode": {'method': 'POST', 'path': '/site/addpromocode', 'result_key': 'PromoCode'},
        "post_site_deactivatepromocode": {'method': 'POST', 'path': '/site/deactivatepromocode'},
        "post_site_updateclientindex": {'method': 'POST', 'path': '/site/updateclientindex',
                                        'result_key': 'ClientIndexID'},
        "post_staff_addstaff": {'method': 'POST', 'path': '/staff/addstaff', 'result_key': 'Staff'},
        "post_staff_assignsessiontype": {'method': 'POST', 'path': '/staff/assignsessiontype', 'result_key': 'StaffId'},
        "post_staff_staffavailability": {'method': 'POST', 'path': '/staff/staffavailability'},
        "post_staff_updatestaff": {'method': 'POST', 'path': '/staff/updatestaff', 'result_key': 'Staff'},
        "post_staff_updatestaffpermissions": {'method': 'POST', 'path': '/staff/updatestaffpermissions',
                                              'result_key': 'UserGroup'},
        "put_appointment_availabilities": {'method': 'PUT', 'path': '/appointment/availabilities',
                                           'result_key': 'StaffMembers'},
        "put_pickaspot_reservation_by_pathinfo": {'method': 'PUT', 'path': '/pickaspot/v1/reservation/{pathInfo}',
                                                  'result_key': 'Reservation'},
        "put_sale_products": {'method': 'PUT', 'path': '/sale/products', 'result_key': 'Products'},
        "put_sale_services": {'method': 'PUT', 'path': '/sale/services', 'result_key': 'Services'},
        "put_sale_updatesaledate": {'method': 'PUT', 'path': '/sale/updatesaledate', 'result_key': 'Sale'},
    }

    def __getattr__(self, name):
        """
        Allow dynamic calls to endpoints like:
            api.get_sale_products(params={...})
            api.get_pickaspot_class_by_classid(classId=123)
        """

        if name in self.ENDPOINTS:
            endpoint_info = self.ENDPOINTS[name]

            def wrapper(params=None, payload=None, **kwargs):
                # Fill placeholders in URL from kwargs
                url = endpoint_info['path']
                for k, v in kwargs.items():
                    placeholder = "{" + k + "}"
                    if placeholder in url:
                        url = url.replace(placeholder, str(v))

                full_url = f"{self.BASE_URL}{url}"
                return self._request(endpoint_info["method"], full_url, params=params, data=payload)

            return wrapper

        raise AttributeError(f"{self._name}: unknown method '{name}'")

    # ----------------------------
    # Context helpers
    # ----------------------------
    def _get_company(self):
        return self.env.company

    # ----------------------------
    # Private helpers
    # ----------------------------
    def _get_endpoint_info(self, key):
        """
        Retrieve endpoint info from ENDPOINTS dict.
        Raises UserError if key is unknown.
        Optionally returns full URL.
        """
        info = self.ENDPOINTS.get(key)
        if not info:
            raise UserError(_("Unknown Mindbody endpoint key: %s") % key)
        info = info.copy()
        info['url'] = f"{self.BASE_URL}{info['path']}"
        return info

    # ----------------------------
    # Token & Credential Handling
    # ----------------------------
    def _validate_credentials(self):
        company = self._get_company()
        if not company.mindbody_enabled:
            raise UserError(_("Mindbody integration is not enabled for this company."))
        missing = [f for f in ["mindbody_api_key", "mindbody_site_id",
                               "mindbody_username", "mindbody_password"] if not getattr(company, f)]
        if missing:
            raise UserError(_("Mindbody credentials missing: %s") % ", ".join(missing))

    def _is_token_expired(self):
        company = self._get_company()
        return not company.mindbody_access_token or not company.mindbody_token_expires_at \
            or fields.Datetime.now() >= company.mindbody_token_expires_at

    def issue_token(self):
        company = self._get_company()
        self._validate_credentials()
        url = f"{self.BASE_URL}/usertoken/issue"
        payload = {
            "Username": company.mindbody_username,
            "Password": company.mindbody_password,
        }
        headers = {
            "Api-Key": company.mindbody_api_key,
            "SiteId": str(company.mindbody_site_id),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.exception("Mindbody token issue failed")
            raise UserError(_("Failed to get Mindbody token: \n%s") % e)

        data = response.json()
        token = data.get("AccessToken")
        expires_in = data.get("ExpiresIn", 3600)
        if not token:
            raise UserError(_("Mindbody token not returned: %s") % data)

        # Save token and expiry (minus 60s buffer)
        expires_at = fields.Datetime.now() + timedelta(seconds=expires_in - 60)
        company.sudo().write({
            "mindbody_access_token": token,
            "mindbody_token_expires_at": expires_at,
        })
        return token

    def renew_token(self):
        """Renew existing token if supported by API"""
        company = self._get_company()
        if not company.mindbody_access_token:
            return self.issue_token()
        url = f"{self.BASE_URL}/usertoken/renew"
        headers = self._headers(with_auth=True)
        try:
            response = requests.post(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.exception("Mindbody token renewal failed")
            return self.issue_token()  # fallback
        data = response.json()
        token = data.get("AccessToken")
        expires_in = data.get("ExpiresIn", 3600)
        company.sudo().write({
            "mindbody_access_token": token,
            "mindbody_token_expires_at": fields.Datetime.now() + timedelta(seconds=expires_in - 60),
        })
        return token

    def revoke_token(self):
        """Revoke current token"""
        company = self._get_company()
        if not company.mindbody_access_token:
            return
        url = f"{self.BASE_URL}/usertoken/revoke"
        headers = self._headers(with_auth=True)
        try:
            response = requests.delete(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.exception("Mindbody token revoke failed: %s", e)
        finally:
            company.sudo().write({
                "mindbody_access_token": False,
                "mindbody_token_expires_at": False,
            })

    def _ensure_token(self):
        """Ensure valid token exists"""
        if self._is_token_expired():
            return self.issue_token()
        return self._get_company().mindbody_access_token

    # ----------------------------
    # Request Helpers
    # ----------------------------
    def _headers(self, with_auth=True):
        company = self._get_company()
        headers = {
            "Api-Key": company.mindbody_api_key,
            "SiteId": str(company.mindbody_site_id),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if with_auth:
            headers["Authorization"] = f"Bearer {self._ensure_token()}"
        return headers

    def _request(self, method, url, params=None, data=None, timeout=15, retry=True):
        try:
            response = requests.request(method, url, headers=self._headers(), params=params, json=data, timeout=timeout)
        except requests.exceptions.RequestException as e:
            _logger.exception("Mindbody request failed: %s", url)
            raise UserError(_("Mindbody request failed: %s") % e)

        # Token expired
        if response.status_code == 401 and retry:
            _logger.info("Mindbody token expired, refreshing")
            self.issue_token()
            return self._request(method, url, params, data, retry=False)

        # Throttle
        if response.status_code == 429 and retry:
            _logger.warning("Mindbody rate limit reached, retrying after 2s")
            time.sleep(2)
            return self._request(method, url, params, data, retry=False)

        if response.status_code >= 400:
            _logger.error("Mindbody API Error [%s]: %s", response.status_code, response.text)
            raise UserError(_("Mindbody API Error [%s]: %s") % (response.status_code, response.text))

        return response.json()

    # ----------------------------
    # Public Endpoint Calls
    # ----------------------------
    def call_endpoint(self, key, params=None, payload=None):
        """Generic API call using ENDPOINTS dict"""
        info = self._get_endpoint_info(key)
        return self._request(info["method"], info["url"], params=params, data=payload)

    def fetch_all(self, key, params=None, page_size=200, max_pages=100):
        """
        Fetch all records from a Mindbody endpoint, handling Offset/Limit pagination safely.

        Args:
            key (str): Endpoint key from ENDPOINTS dict.
            params (dict, optional): Extra query parameters.
            page_size (int, optional): Number of records per page.
            max_pages (int, optional): Maximum number of pages to fetch to prevent infinite loops.

        Returns:
            list: All fetched records from the endpoint.
        """
        info = self._get_endpoint_info(key)
        result_key = info.get("result_key")
        if not result_key:
            raise UserError(_("No result_key defined for endpoint: %s") % key)

        all_items = []
        offset = 0
        page_count = 0

        while page_count < max_pages:
            p = params.copy() if params else {}
            p.update({"Offset": offset, "Limit": page_size})

            data = self._request(info["method"], info["url"], params=p)
            items = data.get(result_key) or []

            if not items:
                _logger.info("No more records found at offset %d for endpoint %s", offset, key)
                break

            all_items.extend(items)
            offset += page_size
            page_count += 1

        if page_count == max_pages:
            _logger.warning("Reached max_pages=%d while fetching %s, result may be partial", max_pages, key)

        _logger.info("Fetched total %d records from endpoint %s", len(all_items), key)
        return all_items
