from rest_framework.views import APIView


class WhatsAppMessageWebhookView(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        print(data)
        return data
        # application = cache.get_or_set(app, System.objects.get(name=app))
        # template = Template(application.redirect_to)
        # context = Context({'id': orderId})
        # url = template.render(context)
        # print(url)
        # response = requests.post(url, json=data)
        # if response.status_code >= 500:
        #     return JsonResponse({})
        # response.raise_for_status()
        # # success_response = dict(Success=True, Status=1, Resultmsg="OK")
        # print(response.json())
        # return JsonResponse(response.json(), safe=False)
