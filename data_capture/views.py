import json
from functools import wraps
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.defaultfilters import pluralize

from . import forms
from .schedules import registry
from frontend import ajaxform


def step_ctx(step_number, ctx=None):
    final_ctx = {
        'step_number': step_number,
        'NUM_STEPS': NUM_STEPS
    }
    if ctx:
        final_ctx.update(ctx)
    return final_ctx


def add_generic_form_error(request, form):
    messages.add_message(
        request, messages.ERROR,
        'Oops, please correct the error{} below and try again.'
            .format(pluralize(form.errors))
    )


@login_required
def step_1(request):
    if request.method == 'GET':
        form = forms.Step1Form()
    elif request.method == 'POST':
        form = forms.Step1Form(request.POST, request.FILES)

        if form.is_valid():
            request.session['data_capture:schedule'] = \
                form.cleaned_data['schedule']
            request.session['data_capture:gleaned_data'] = \
                registry.serialize(form.cleaned_data['gleaned_data'])

            return ajaxform.redirect(request, 'data_capture:step_2')
        else:
            add_generic_form_error(request, form)

    return ajaxform.render(
        request,
        context=step_ctx(1, {
            'form': form,
            'show_debug_ui': settings.DEBUG and not settings.HIDE_DEBUG_UI
        }),
        template_name='data_capture/step_1.html',
        ajax_template_name='data_capture/step_1_form.html',
    )


def gleaned_data_required(f):
    @wraps(f)
    def wrapper(request):
        d = request.session.get('data_capture:gleaned_data')

        if d is None:
            return redirect('data_capture:step_1')

        return f(request, registry.deserialize(d))
    return wrapper


@login_required
@gleaned_data_required
def step_2(request, gleaned_data):
    preferred_schedule = registry.get_class(
        request.session['data_capture:schedule']
    )

    return render(request, 'data_capture/step_2.html', step_ctx(2, {
        'gleaned_data': gleaned_data,
        'is_preferred_schedule': isinstance(gleaned_data, preferred_schedule),
        'preferred_schedule': preferred_schedule,
    }))


@login_required
@gleaned_data_required
def step_3(request, gleaned_data):
    if not gleaned_data.valid_rows:
        # The user may have manually changed the URL or something to
        # get here. Push them back to the last step.
        return redirect('data_capture:step_2')

    if request.method == 'GET':
        form = forms.Step3Form()
    elif request.method == 'POST':
        form = forms.Step3Form(request.POST)
        if form.is_valid():
            price_list = form.save(commit=False)
            price_list.schedule = registry.get_classname(gleaned_data)
            price_list.submitter = request.user
            price_list.serialized_gleaned_data = json.dumps(
                request.session.get('data_capture:gleaned_data')
            )
            price_list.save()
            gleaned_data.add_to_price_list(price_list)

            del request.session['data_capture:gleaned_data']

            return redirect('data_capture:step_4')
        else:
            add_generic_form_error(request, form)

    return render(request, 'data_capture/step_3.html', step_ctx(3, {
        'form': form
    }))


def step_4(request):
    return render(request, 'data_capture/step_4.html', step_ctx(4))


def get_num_steps():
    for i in range(1, 999):
        if 'step_%d' % i not in globals():
            return i - 1


NUM_STEPS = get_num_steps()
